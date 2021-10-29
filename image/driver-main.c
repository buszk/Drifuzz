#include <fcntl.h>
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <sys/wait.h>
#define KCOV_INIT_TRACE _IOR('c', 1, unsigned long)
#define KCOV_ENABLE _IO('c', 100)
#define KCOV_DISABLE _IO('c', 101)
#define COVER_SIZE (64 << 10)

#define KCOV_TRACE_PC 0
#define KCOV_TRACE_CMP 1

#define BITMAP_SIZE 65536

static char *target = NULL;
static char *prog = NULL;

void exec_init() {
    int fd;
    uint64_t act = 5;
    fd = open("/dev/drifuzz", O_WRONLY);
    write(fd, &act, sizeof(act));
    close(fd);
}

void exec_exit() {
    int fd;
    uint64_t act = 6;
    fd = open("/dev/drifuzz", O_WRONLY);
    write(fd, &act, sizeof(act));
    close(fd);
}

void req_reset() {
    int fd;
    uint64_t payload[] = {10};
    fd = open("/dev/drifuzz", O_WRONLY);
    write(fd, &payload, sizeof(payload));
    close(fd);
}

void get_drifuzz_args() {
    int fd;
    uint64_t len;
    
    fd = open("/dev/drifuzz", O_RDONLY);

    /* get target */
    if (read(fd, &len, sizeof(uint64_t)) < 0)
        perror("Getting target");
    printf("target length: %ld\n", len);
    if (len > 0)
        target = malloc(len);
    if (read(fd, target, len) < 0)
        perror("Getting target");
    
    /* get prog */
    if (read(fd, &len, sizeof(uint64_t)) < 0)
        perror("Getting prog");
    printf("prog length: %ld\n", len);
    if (len > 0)
        prog = malloc(len);
    if (read(fd, prog, len) < 0)
        perror("Getting prog");
    
    printf("drifuzz target: %s\n", target ? target : "none");
    printf("drifuzz prog: %s\n", prog ? prog : "none");
    close (fd);

}

int main(int argc, char **argv) {
    int fd;
    unsigned long *cover, n, i;
    char cmd[128];
    
    system("[ -e /dev/drifuzz ] || mknod /dev/drifuzz c 248 0");

    get_drifuzz_args();
    // target = (char*) "alx";
    // prog = (char*) "init";

    if (!(target && prog))
        return 0;

    /* A single fd descriptor allows coverage collection on a single
    * thread.
    */
    fd = open("/sys/kernel/debug/kcov", O_RDWR);
    if (fd == -1)
        perror("open"), exit(1);
    /* Setup trace mode and trace size. */
    if (ioctl(fd, KCOV_INIT_TRACE, BITMAP_SIZE/sizeof(unsigned long)))
        perror("ioctl"), exit(1);
    /* Mmap buffer shared between kernel- and user-space. */
    cover = (unsigned long *)mmap(NULL, BITMAP_SIZE,
                                PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ((void *)cover == MAP_FAILED)
        perror("mmap"), exit(1);
    
    /* For tracing via qemu nmi cmd */
    system("sysctl kernel.unknown_nmi_panic=1");
    system("echo '1' > /sys/module/rcupdate/parameters/rcu_cpu_stall_suppress");

    /* Prepare by loading all depended modules */
    snprintf(cmd, sizeof(cmd), "/root/prog-prepare.sh %s", target);
    printf("%s\n", cmd);
    system(cmd);
    memset(cmd, 0, sizeof(cmd));

    if (ioctl(fd, KCOV_ENABLE, KCOV_TRACE_PC))
        perror("ioctl"), exit(1);
    memset(cover, 255, BITMAP_SIZE);
    exec_init();
    
    snprintf(cmd, sizeof(cmd), "/root/prog-%s.sh %s", prog, target);
    printf("%s\n", cmd);
    system(cmd);

    if (ioctl(fd, KCOV_DISABLE, 0))
        perror("ioctl"), exit(1);
    exec_exit();

    /* Free resources. */
    if (munmap(cover, BITMAP_SIZE/sizeof(unsigned long)))
    perror("munmap"), exit(1);
    if (close(fd))
    perror("close"), exit(1);
    
    req_reset();
    return 0;
}
