"""This module implements a bit-level binary reader."""

from os.path import isfile


class BitReader:
    """Bit-by-bit binary reader."""

    def __init__(self, file_name: str) -> None:
        """
        Args:
            file_name:
                Input file name without extension.
                The reader will look for a file named file_name.sdfl
        """

        self.file_name = f"{file_name}.sdfl"

        if not isfile(self.file_name):
            raise FileNotFoundError(f"file not found: {self.file_name}")

        self.file = open(self.file_name, "rb")

        self.is_open = True

        self.byte = 0
        self.remaining_bits_in_byte = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _ensure_open(self) -> None:
        """Raise if reader is closed."""

        if not self.is_open:
            raise ValueError("I/O operation on closed BitReader")

    def _read_byte(self) -> None:
        """Load the next byte from the file."""

        byte = self.file.read(1)

        if byte == b"":
            raise EOFError("unexpected end of file")

        self.byte = byte[0]
        self.remaining_bits_in_byte = 8

    def read_bit(self) -> int:
        """Read a single bit and return it as 0 or 1."""

        return self.read_bits(1)

    def read_bits(self, num_bits: int) -> int:
        """
        Read num_bits bits and return them as an integer.

        Bits are read MSB-first, matching the write order of BitWriter.

        Args:
            num_bits:
                Number of bits to read. Must be non-negative.

        Returns:
            Integer value of the bits read.

        Raises:
            ValueError: if num_bits is negative or the reader is closed.
            EOFError: if the file is exhausted before num_bits bits are read.
        """

        self._ensure_open()

        if num_bits < 0:
            raise ValueError("num_bits must be non-negative")

        number = 0

        for i in range(num_bits - 1, -1, -1):

            if self.remaining_bits_in_byte == 0:
                self._read_byte()

            # shift the byte so that the bit we want is at pos 0 then extract it
            bit = (self.byte >> (self.remaining_bits_in_byte - 1)) & 1

            # place the bit in the correct position in the result
            number |= bit << i

            self.remaining_bits_in_byte -= 1

        return number

    def _byte_flush(self) -> str:
        return bin(self.byte)[2:]

    def read_rest(self) -> str:
        """read the rest of the file after successfully reading the metadata.

        Returns:
            str: the rest of the data in the file represented as a string.
        """
        piece1 = self._byte_flush()
        piece2 = "".join(format(byte, "08b") for byte in self.file.read())
        return piece1 + piece2

    def close(self) -> None:
        """Close the file."""

        if not self.is_open:
            return

        self.file.close()
        self.is_open = False


if __name__ == "__main__":

    from BitWriter import BitWriter

    def _test_bit_reader():

        # first write a known file using BitWriter
        writer = BitWriter("test_rw", overwrite=True)
        writer.write_bits("10101010")  # 0xAA
        writer.write_bits("1111-0000")  # 0xF0
        writer.write_bits("0000 1111")  # 0x0F
        writer.write_bits("11")  # 0xC0 after padding
        writer.close()

        # now read it back with BitReader
        reader = BitReader("test_rw")

        print(f"Testing {reader.file_name}...")

        results = [
            reader.read_bits(8),  # should be 0xAA = 170
            reader.read_bits(8),  # should be 0xF0 = 240
            reader.read_bits(8),  # should be 0x0F = 15
            reader.read_bits(8),  # should be 0xC0 = 192
        ]

        reader.close()

        expected = [0xAA, 0xF0, 0x0F, 0xC0]

        if results == expected:
            print("PASSED")
        else:
            print(
                "FAILED\n"
                f"Expected: {[hex(x) for x in expected]}\n"
                f"Got:      {[hex(x) for x in results]}"
            )

    _test_bit_reader()
