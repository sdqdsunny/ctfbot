// Simple CTF Reverse Challenge: XOR Encryption
// Compile: gcc -o simple_reverse simple_reverse.c -no-pie

#include <stdio.h>
#include <string.h>

void check_flag(const char *input) {
  // XOR encrypted flag with key 0x42
  unsigned char encrypted[] = {0x24, 0x2e, 0x23, 0x25, 0x39, 0x3a, 0x72,
                               0x30, 0x1d, 0x30, 0x71, 0x34, 0x71, 0x30,
                               0x31, 0x71, 0x1d, 0x2f, 0x76, 0x31, 0x36,
                               0x71, 0x30, 0x3f, 0x00};

  int len = strlen((char *)encrypted);

  if ((int)strlen(input) != len) {
    printf("Wrong length! Expected %d characters.\n", len);
    return;
  }

  for (int i = 0; i < len; i++) {
    if ((input[i] ^ 0x42) != encrypted[i]) {
      printf("Wrong! Try harder.\n");
      return;
    }
  }

  printf("Correct! You got the flag!\n");
}

int main() {
  char input[128];
  printf("Enter the flag: ");
  fgets(input, sizeof(input), stdin);

  // Remove newline
  int len = strlen(input);
  if (len > 0 && input[len - 1] == '\n') {
    input[len - 1] = '\0';
  }

  check_flag(input);
  return 0;
}
