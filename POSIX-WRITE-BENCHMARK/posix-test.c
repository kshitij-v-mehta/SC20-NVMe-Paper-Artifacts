/*
 *  Author: Kshitij Mehta
 *  Benchmark for testing file io speed.
 *
 *  Run application as ./<exe> <total_amount_of_data> <block_size_per_io> 
 *  e.g. mpirun -np 4 ./bench 100G 64MB
 *
 *  Total amount of data must not be less than 1MB.
 *
 *  Bechmark uses the `io` function for writing data.
 *  A file per MPI rank is created.
 *  Each process ios <total_amount_of_data>/number_of_processes.
 *  Each process issues ios of the size <block_size_per_process>.
 *
 *  Sleep interval between ios is 32 sec for 64GB blocks, 16 sec for 32GB blocks, 8 sec for 16GB blocks, and so on.
 *  Sleep interval between ios is 1 sec.
 *  Sleep interval between iterations is 10 sec.
 *  For file sizes per process greater than 10 GB, sleep interval between iterations is 30 sec.
 *
 *  Example:
 *      4 MPI processes, total_amount_of_data = 10 GB, block_size_per_process = 64 MB.
 *
 *      Each process ios (10 GB/4) = 2.5 GB of data.
 *      Each process issues 64 MB ios for a total of (2.5G/64M) = 64 times.
 *      Files created: io_test.out.0, io_test.out.1, io_test.out.2, io_test.out.3
 * 
 *  Open, io, and close operations are timed separately (excluding sleep).
 *
 *  For each timestep, each ior ios out its timing information to a separate file.
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <mpi.h>

#define TWO_GB 2147483648l

int num_iter = 1;

void print_usage()
{
    fprintf(stdout, "Run as: -t <total output data> -b <block size> -f <output filename>\n");
    return;
}

void read_args(int argc, char **argv, long *filesize, long *blocksize, char* filename)
{
    int c, t=0, b=0, f=0;
    char *size_mg;
    while ((c = getopt (argc, argv, "t:b:f:")) != -1)
        switch (c)
        {
            // Get filesize
            case 't':
                t=1;
                *filesize = strtol(optarg, &size_mg, 10);
                if (size_mg[0] == 'm' || size_mg[0] == 'M')
                    *filesize *= 1048576;
                else if (size_mg[0] == 'g' || size_mg[0] == 'G')
                    *filesize *= 1073741824;
                else if (size_mg[0] == 't' || size_mg[0] == 'T')
                    *filesize *= 1073741824l * 1024;
                break;
           
            // Get blocksize
            case 'b':
                b=1;
                *blocksize = strtol(optarg, &size_mg, 10);
                if (size_mg[0] == 'm' || size_mg[0] == 'M')
                    *blocksize *= 1048576;
                else if (size_mg[0] == 'g' || size_mg[0] == 'G')
                    *blocksize *= 1073741824;
                break;

            case 'f':
                f=1;
                strcpy(filename, optarg);
                break;

            default:
                print_usage();
                exit(1);
                break;
        }

        if (!t || !b || !f) {
            print_usage();
            exit(1);
        }
    return ;
}

int main(int argc, char** argv)
{
    char filename[1024] = {0};
    char local_filename[128] = {0};
    char local_filename_ext[32] = {0};
    char *buffer = NULL;
    long bytes_transferred, bytes_remaining, blocksize = 0;
    long filesize = 0;
    long local_filesize = 0;
    int rank, size;
    char *rank_str;
    int fd;
    long i, j;
    double open_timer_start, open_elapsed_time = 0.0;
    double close_timer_start, close_elapsed_time = 0.0;
    double io_timer_start, io_timer_stop, io_elapsed_time = 0.0;
    double global_io_timer_start, global_io_timer_stop;
    double local_total_time = 0.0;
    double global_open_time = 0.0, global_close_time = 0.0, global_io_time = 0.0, global_total_time = 0.0;
    double bandwidth;
    int sleep_interval = 0;
    int stripe_offset = -1;

    MPI_Init (&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    read_args(argc, argv, &filesize, &blocksize, filename);
    
    strncpy(local_filename, filename, strlen(filename));
    sprintf(local_filename_ext, ".%d", rank);
    strcat(local_filename, local_filename_ext);

    local_filesize = filesize/size;
    
    if (rank == 0) printf("Total data size: %ld, outfile: %s, per step block size: %ld, local_filesize: %ld\n", 
        filesize, local_filename, blocksize, local_filesize);
    fflush(stdout);
    
    // Set sleep interval
    sleep_interval = blocksize/1073741824/2;
    if (sleep_interval == 0) sleep_interval = 1;
    //if (rank == 0) printf("Sleep interval: %d seconds\n", sleep_interval);
    fflush(stdout);

    // Malloc buffer
    if (NULL == (buffer = malloc(blocksize))) {
        perror ("Could not allocate buffer");
        exit(1);
    } 

    // Open file for writing
    open_timer_start = MPI_Wtime();
#ifdef WRITE
    fd = open (local_filename, O_CREAT|O_WRONLY, 0644);
#else
    fd = open (local_filename, O_RDONLY, 0644);
#endif
    if (fd < 0) {
        perror ("Error: Could not open file");
        exit(1);
    }
    open_elapsed_time += MPI_Wtime() - open_timer_start;

    //printf("Rank %d open time: %.2f\n", rank, open_elapsed_time);
    //fflush(stdout);

    for (j=0; j<blocksize; j++)
        buffer[j] = i%127;
        
    MPI_Barrier(MPI_COMM_WORLD);
    global_io_timer_start = MPI_Wtime();

    // Iterate over block ios
    for(i=0; i<local_filesize/blocksize; i++) {
        io_timer_start = MPI_Wtime();
        
        bytes_transferred = 0;
        bytes_remaining = blocksize;
        while (bytes_remaining > 0) {
#ifdef WRITE
            bytes_transferred = write(fd, &buffer[blocksize-bytes_remaining], bytes_remaining); 
#else
            bytes_transferred = read(fd, &buffer[blocksize-bytes_remaining], bytes_remaining); 
#endif
            if (bytes_transferred == -1) {
                perror("Write failed!");
                MPI_Abort(MPI_COMM_WORLD, -1);
            }
            bytes_remaining -= bytes_transferred;
        }
    
        io_timer_stop = MPI_Wtime();
        printf("Rank: %d, step: %d, io time: %.4f\n", rank, i, io_timer_stop - io_timer_start);
        fflush(stdout);
        
        //MPI_Barrier(MPI_COMM_WORLD);
        //sleep (sleep_interval);
    }
    
    MPI_Barrier(MPI_COMM_WORLD);
    global_io_timer_stop = MPI_Wtime();
    io_elapsed_time += global_io_timer_stop - global_io_timer_start;

    // Close file
    close_timer_start = MPI_Wtime();
    close(fd);
    close_elapsed_time += MPI_Wtime() - close_timer_start;

    //printf("Rank: %d, close time: %.2f\n", rank, close_elapsed_time); 
    //fflush(stdout);

    local_total_time = open_elapsed_time + io_elapsed_time + close_elapsed_time;
    if (rank == 0)
        printf("Rank: %d, open time: %.2f, total io time: %.2f, close time: %.2f\n", 
                rank, open_elapsed_time, io_elapsed_time, close_elapsed_time);

    // Cleanup
    free (buffer);
    MPI_Finalize();
    return 0;
}

