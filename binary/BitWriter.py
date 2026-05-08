"""This module implements BinaryWriter class that handles data bit by bit."""

from os.path import isfile

BUFFER_SIZE = 4096  # 4KiB buffer for efficient system calls


class BitWriter:
    """Buffered bit by bit binary writer"""

    def __init__(self, file_name: str) -> None:

        # file_name handling
        self.file_name = f"{file_name}.sdfl"
        if isfile(self.file_name):

            delete_file = input(
                f"do you want to overwrite the existing file:{self.file_name}(y/n) "
            )

            while True:
                match delete_file.lower():
                    case "y":
                        open(self.file_name, "wb").close()
                        break
                    case "n":
                        exit(0)
                    case _:
                        delete_file = input(
                            f"do you want to overwrite the existing file:{self.file_name}(y/n)"
                        )
        try:
            self.file = open(self.file_name, "wb")
            self.is_open = True
        except OSError:
            self.is_open = False
            print(f"failed to open the  file f{self.file_name}.")

        self.remaining_bits_in_byte = 8
        self.byte = 0
        self.buffer = bytearray(BUFFER_SIZE)
        self.used_bytes_in_buffer = 0

    @staticmethod
    def _valid_bit_string(bits: str) -> bool:
        for index, bit in enumerate(bits):
            if bit not in "01- ":
                print(f"invalid bit:{bit} at index:{index}")
                print(
                    "nothing was wrote to the file and the buffer is at it was before this call"
                )
                return False
        return True

    def write_bits(self, bits: str) -> None:
        """write the given bits to the buffer and when the buffer is full it
           will automatically write it to the file.

            Note: the function only accepts these characters as input "0" "1"
            "-" " ", "-" and " " are just ignored and made for ease of use

        Args:
            bits (str): the bit string you want to write eg "1101-0111 1111 0000"
        """
        if BitWriter._valid_bit_string(bits) and self.is_open:
            for bit in bits:
                if bit == "-" or bit == " ":
                    continue
                else:
                    if bit == "1":
                        self.byte |= 1 << (self.remaining_bits_in_byte - 1)
                    self.remaining_bits_in_byte -= 1

                    if self.remaining_bits_in_byte == 0:
                        self._full_byte_handling()

                        if self.used_bytes_in_buffer == BUFFER_SIZE:
                            self.file.write(self.buffer)
                            self.used_bytes_in_buffer = 0
        elif not self.is_open:
            print("The file is closed don't use this object anymore create a new one")

    def _full_byte_handling(self):
        self.buffer[self.used_bytes_in_buffer] = self.byte
        self.byte = 0
        self.used_bytes_in_buffer += 1
        self.remaining_bits_in_byte = 8

    def flush(self):
        """
        write the the buffer even if it's not full to the system

        Note: you must use the flush function that the class provided or
        other wise it's not guaranteed that you will find the data in the
        file.
        """

        if self.remaining_bits_in_byte < 8:
            self._full_byte_handling()
        if self.used_bytes_in_buffer > 0:
            self.file.write(self.buffer[: self.used_bytes_in_buffer])
            self.file.flush()
            self.used_bytes_in_buffer = 0

    def close_writer(self):
        """flush the internal buffer and close the opened file"""
        if self.is_open:
            self.flush()
            self.file.close()
            self.is_open = False
        else:
            print("the file is already closed.")


if __name__ == "__main__":
    test_writer = BitWriter("test")
    test_writer.write_bits("11110101")
    # test_writer.flush()
