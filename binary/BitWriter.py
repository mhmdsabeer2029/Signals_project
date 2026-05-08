"""This module implements a buffered bit-level binary writer."""

from os.path import isfile


class BitWriter:
    """Buffered bit-by-bit binary writer."""

    def __init__(
        self,
        file_name: str,
        overwrite: bool = False,
        buffer_size: int = 4096,
    ) -> None:
        """
        Args:
            file_name:
                Output file name without extension.

            overwrite:
                If False and the file already exists, raise FileExistsError.

            buffer_size:
                Internal byte buffer size.
        """

        if buffer_size <= 0:
            raise ValueError("buffer_size must be greater than 0")

        self.file_name = f"{file_name}.sdfl"

        if not overwrite and isfile(self.file_name):
            raise FileExistsError(f"file already exists: {self.file_name}")

        # Let OSError propagate naturally if opening fails.
        self.file = open(self.file_name, "wb")

        self.is_open = True

        self.remaining_bits_in_byte = 8
        self.byte = 0

        self.buffer_size = buffer_size
        self.buffer = bytearray(buffer_size)
        self.used_bytes_in_buffer = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _validate_bits(bits: str) -> None:
        """Validate bit string input."""

        for index, bit in enumerate(bits):
            if bit not in "01- ":
                raise ValueError(f"invalid bit {bit!r} at index {index}")

    def _ensure_open(self) -> None:
        """Raise if writer is closed."""

        if not self.is_open:
            raise ValueError("I/O operation on closed BitWriter")

    def write_bits(self, bits: str) -> None:
        """
        Write bits to the internal buffer.

        Accepted characters:
            '0', '1', '-', ' '

        '-' and ' ' are ignored for readability.

        Example:
            writer.write_bits("1010-1111 0000")
        """

        self._ensure_open()
        self._validate_bits(bits)

        for bit in bits:

            if bit in "- ":
                continue

            if bit == "1":
                self.byte |= 1 << (self.remaining_bits_in_byte - 1)

            self.remaining_bits_in_byte -= 1

            if self.remaining_bits_in_byte == 0:
                self._commit_byte()

                if self.used_bytes_in_buffer == self.buffer_size:
                    self.file.write(self.buffer)
                    self.used_bytes_in_buffer = 0

    def _commit_byte(self) -> None:
        """Commit the current byte into the buffer."""

        self.buffer[self.used_bytes_in_buffer] = self.byte

        self.byte = 0
        self.remaining_bits_in_byte = 8
        self.used_bytes_in_buffer += 1

    def flush(self) -> None:
        """
        Flush internal buffer to file.

        Partial bytes are padded with zeros on the right.
        """

        self._ensure_open()

        if self.remaining_bits_in_byte < 8:
            self._commit_byte()

        if self.used_bytes_in_buffer > 0:
            self.file.write(self.buffer[: self.used_bytes_in_buffer])

            self.file.flush()

            self.used_bytes_in_buffer = 0

    def close(self) -> None:
        """Flush buffered data and close the file."""

        if not self.is_open:
            return

        self.flush()
        self.file.close()

        self.is_open = False


if __name__ == "__main__":

    def _test_bit_writer():

        writer = BitWriter(
            "test_output",
            overwrite=True,
        )

        print(f"Testing {writer.file_name}...")

        writer.write_bits("10101010")  # 0xAA
        writer.write_bits("1111-0000")  # 0xF0
        writer.write_bits("0000 1111")  # 0x0F
        writer.write_bits("11")  # 0xC0 after padding

        writer.close()

        with open(writer.file_name, "rb") as f:
            content = f.read()

        expected = bytes([0xAA, 0xF0, 0x0F, 0xC0])

        if content == expected:
            print("PASSED")
        else:
            print(
                "FAILED\n" f"Expected: {expected.hex()}\n" f"Got:      {content.hex()}"
            )

    _test_bit_writer()
