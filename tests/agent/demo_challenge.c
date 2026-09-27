#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// MD5 of "admin123" is 0192023a7bbd73250516f069df18b500
const char* target_hash = "0192023a7bbd73250516f069df18b500";

void check_logic(char* input) {
    if (strlen(input) != 8) {
        printf("Invalid length\n");
        return;
    }
    // Deep logic for angr to solve
    if (input[0] + input[1] == 200 && input[2] * input[3] == 10000) {
        if (strcmp(input, "admin123") == 0) {
             printf("Flag: flag{swarm_gpu_reasoning_success}\n");
        } else {
             printf("Access Denied\n");
        }
    } else {
        printf("Keep trying\n");
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: %s <password>\n", argv[0]);
        return 1;
    }
    check_logic(argv[1]);
    return 0;
}
