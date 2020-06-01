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

void submit_kcov_trace(void *ptr, size_t size) {
  int fd;
  uint64_t payload[] = {8, (uint64_t)ptr, (uint64_t)size};
  fd = open("/dev/drifuzz", O_WRONLY);
  write(fd, &payload, sizeof(payload));
  close(fd);
}

void req_reset() {
  int fd;
  uint64_t payload[] = {10};
  fd = open("/dev/drifuzz", O_WRONLY);
  write(fd, &payload, sizeof(payload));
  close(fd);
}

int main(int argc, char **argv) {
  int fd;
  unsigned long *cover, n, i;

  /* A single fd descriptor allows coverage collection on a single
   * thread.
   */
  fd = open("/sys/kernel/debug/kcov", O_RDWR);
  if (fd == -1)
    perror("open"), exit(1);
  /* Setup trace mode and trace size. */
  if (ioctl(fd, KCOV_INIT_TRACE, COVER_SIZE))
    perror("ioctl"), exit(1);
  /* Mmap buffer shared between kernel- and user-space. */
  cover = (unsigned long *)mmap(NULL, COVER_SIZE * sizeof(unsigned long),
                                PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  if ((void *)cover == MAP_FAILED)
    perror("mmap"), exit(1);

  system("[ -e /dev/drifuzz ] || mknod /dev/drifuzz c 248 0");

  for (int i = 0; i < 4; i++) {
    if (ioctl(fd, KCOV_ENABLE, KCOV_TRACE_PC))
      perror("ioctl"), exit(1);
    __atomic_store_n(&cover[0], 0, __ATOMIC_RELAXED);
    exec_init();
    system("modprobe alx");
    system("ip link set dev enp0s3 up");
    sleep(0.5);
    system("ip link set dev enp0s3 down");
    system("rmmod alx");
    if (ioctl(fd, KCOV_DISABLE, 0))
      perror("ioctl"), exit(1);
    n = __atomic_load_n(&cover[0], __ATOMIC_RELAXED);
    printf("%ld traces detected first: %lx\n", n, __atomic_load_n(&cover[1], __ATOMIC_RELAXED));
    exec_exit();
  }

  /* Free resources. */
  if (munmap(cover, COVER_SIZE * sizeof(unsigned long)))
    perror("munmap"), exit(1);
  if (close(fd))
    perror("close"), exit(1);
  req_reset();
  return 0;
}
