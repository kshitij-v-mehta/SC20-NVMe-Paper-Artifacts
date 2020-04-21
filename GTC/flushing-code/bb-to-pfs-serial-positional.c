/*
 *  Author: Kshitij Mehta
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <time.h>
#include <string.h>
#include <mpi.h>


/*
 *
 */
void print_usage(int argc, char **argv)
{
    int i;
    for (i=0; i<argc; i++)
        fprintf(stderr, "%s\n", argv[i]);
    fprintf(stderr, "Run as: %s -i <src> -o <dest> -s <data size to read and write>.\n", argv[0]);
    fflush(stderr);
    return;
}


/*
 *
 */
void read_args(int argc, char **argv, char* src_filename, char* dest_filename, long* datasize)
{
    int c, in=0, out=0, s=0;
    char *eptr;

    while ((c = getopt (argc, argv, "i:o:s:")) != -1)
        switch (c)
        {
            case 'i':
                in=1;
                strcpy(src_filename, optarg);
                break;
            
            case 'o':
                out=1;
                strcpy(dest_filename, optarg);
                break;

            case 's':
                s=1;
                *datasize = strtol(optarg, &eptr, 10);
                break;

            default:
                print_usage(argc, argv);
                exit(1);
                break;
        }

    if (!in || !out || !s) {
        print_usage(argc, argv);
        exit(1);
    }

    return ;
}


/*
 *
 */
void print_args(char* f_in, char *f_out, long datasize) {
    fprintf(stdout, "Input args: in: %s, out: %s, datasize: %ld\n", f_in, f_out, datasize);
    return;
}


/*
 *
 */
int main(int argc, char** argv)
{
    char f_in[128] = {0};
    char f_out[128] = {0};
    char *buffer = NULL;
    long bytes_read=0, bytes_written=0, bytes_remaining=0, blocksize = 0;
    long in_filesize = 0, incoming_size = 0, bytes_transferred = 0, bytes_to_transfer = 0;
    int fd_in, fd_out;
    long begin_at=0, datasize=0, read_offset=0, write_offset=0;
    double t1, t2;

    read_args(argc, argv, f_in, f_out, &datasize);
    print_args(f_in, f_out, datasize);
    
    // Malloc buffer
    blocksize=1073741824; //1GB
    if (datasize > -1 && datasize < blocksize)
        blocksize = datasize;
    if (NULL == (buffer = malloc(blocksize))) {
        perror ("Could not allocate buffer");
        exit(1);
    }
    
    // Open file
    fd_in  = open (f_in, O_RDONLY, 0644);
    fd_out = open (f_out, O_CREAT|O_WRONLY, 0644);
    if (fd_in < 0) {
        fprintf(stderr, "Failed to open %s. ", f_in); 
        perror ("Error: Could not open file for reading. Aborting ...\n");
        exit(1);
    }
    if (fd_out < 0) {
        fprintf(stderr, "Failed to open %s. ", f_out); 
        perror ("Error: Could not open file for writing. Aborting ...\n");
        exit(1);
    }

    // Get the input and output file sizes
    struct stat fbuf;
    fstat(fd_in, &fbuf);
    in_filesize = fbuf.st_size;
    fstat(fd_out, &fbuf);
    begin_at = fbuf.st_size;
 
    if (in_filesize == begin_at) { // If no updates to the file
        printf("Sizes of files %s and %s same at %ld. Returning...\n", f_in, f_out, begin_at);
        goto close;
    }
    if (datasize == -1) { // End of the run. Flush whatever is remaining
        bytes_to_transfer = in_filesize - begin_at;
        if (bytes_to_transfer <= 0) {
            printf("Nothing left to copy between %s and %s. Returning...\n", f_in, f_out);
            goto close;
        }
    }
    else {  // new data available
        incoming_size = in_filesize - begin_at;
        printf("Incoming file size: %ld, data size: %d\n", incoming_size, datasize);
        bytes_to_transfer = datasize;
        if (incoming_size < datasize)
            bytes_to_transfer = incoming_size;
    }

    printf("Bytes to transfer for file %s: %ld\n", f_in, bytes_to_transfer);

    // Start I/O Operation
    bytes_transferred = 0;
    read_offset = begin_at;
    write_offset = begin_at;

    t1 = MPI_Wtime();
    while(bytes_transferred < bytes_to_transfer) {
        
        // Read data, max blocksize per read() call
        bytes_remaining = blocksize;
        if ( (bytes_to_transfer-bytes_transferred) < blocksize)
            bytes_remaining = bytes_to_transfer-bytes_transferred; // trailing bytes for the final loop iteration

        while (bytes_remaining > 0) {
            bytes_read = pread(fd_in, &buffer[blocksize-bytes_remaining], bytes_remaining, read_offset); 
            if (bytes_read == -1) {
                perror("Read failed!");
                exit(-1);
            }
            bytes_remaining -= bytes_read;
            read_offset += bytes_read;
        }
        
        // Write data, max blocksize per write() call
        bytes_remaining = blocksize;
        if ( (bytes_to_transfer-bytes_transferred) < blocksize)
            bytes_remaining = bytes_to_transfer-bytes_transferred; // trailing bytes for the final loop iteration

        while (bytes_remaining > 0) {
            bytes_written = pwrite(fd_out, &buffer[blocksize-bytes_remaining], bytes_remaining, write_offset);
            if (bytes_written == -1) {
                perror("Write failed!");
                exit(-1);
            }
            bytes_remaining -= bytes_written;
            bytes_transferred += bytes_written;
            write_offset += bytes_written;
        }
    }

    t2 = MPI_Wtime();

close:
    // Close file
    close(fd_in);
    close(fd_out);

    // Cleanup
    free (buffer);

    printf("Done. Wrote %d bytes of %s in %f seconds.\n", bytes_transferred, f_in, t2-t1);
    return bytes_transferred;
}

