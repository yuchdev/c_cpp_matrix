#define _POSIX_C_SOURCE 200809L
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <utility>

#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif

class Buffer {
public:
    explicit Buffer(std::size_t size = 0) : size_(size), data_(size ? static_cast<std::uint8_t*>(std::malloc(size)) : nullptr) {
        if (size_ && !data_) {
            std::fprintf(stderr, "malloc failed\n");
            std::exit(1);
        }
        for (std::size_t i = 0; i < size_; ++i) {
            data_[i] = static_cast<std::uint8_t>(i * 131u + 7u);
        }
    }

    ~Buffer() { std::free(data_); }

    Buffer(const Buffer& other) : size_(other.size_), data_(other.size_ ? static_cast<std::uint8_t*>(std::malloc(other.size_)) : nullptr) {
        if (size_ && !data_) {
            std::fprintf(stderr, "malloc failed\n");
            std::exit(1);
        }
        if (size_) std::memcpy(data_, other.data_, size_);
    }

    Buffer& operator=(const Buffer& other) {
        if (this == &other) return *this;
        std::uint8_t* new_data = other.size_ ? static_cast<std::uint8_t*>(std::malloc(other.size_)) : nullptr;
        if (other.size_ && !new_data) {
            std::fprintf(stderr, "malloc failed\n");
            std::exit(1);
        }
        if (other.size_) std::memcpy(new_data, other.data_, other.size_);
        std::free(data_);
        data_ = new_data;
        size_ = other.size_;
        return *this;
    }

    Buffer(Buffer&& other) noexcept : size_(other.size_), data_(other.data_) {
        other.size_ = 0;
        other.data_ = nullptr;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this == &other) return *this;
        std::free(data_);
        data_ = other.data_;
        size_ = other.size_;
        other.data_ = nullptr;
        other.size_ = 0;
        return *this;
    }

    std::size_t size() const noexcept { return size_; }
    const std::uint8_t* data() const noexcept { return data_; }

private:
    std::size_t size_;
    std::uint8_t* data_;
};

NOINLINE static Buffer passthrough_move(Buffer b) {
    return b;
}

NOINLINE static Buffer passthrough_copy(const Buffer& b) {
    return b;
}

NOINLINE static std::uint64_t benchmark_move(std::size_t size, int rounds) {
    Buffer current(size);
    std::uint64_t checksum = 0;
    for (int i = 0; i < rounds; ++i) {
        current = passthrough_move(std::move(current));
        checksum += current.data()[(i * 17) % current.size()];
    }
    return checksum;
}

NOINLINE static std::uint64_t benchmark_copy(std::size_t size, int rounds) {
    Buffer current(size);
    std::uint64_t checksum = 0;
    for (int i = 0; i < rounds; ++i) {
        current = passthrough_copy(current);
        checksum += current.data()[(i * 17) % current.size()];
    }
    return checksum;
}

static double now_sec() {
    timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<double>(ts.tv_sec) + static_cast<double>(ts.tv_nsec) / 1e9;
}

int main() {
    const std::size_t size = 1u << 20; /* 1 MiB */
    const int rounds = 2000;

    double t0 = now_sec();
    std::uint64_t move_checksum = benchmark_move(size, rounds);
    double t1 = now_sec();
    std::uint64_t copy_checksum = benchmark_copy(size, rounds);
    double t2 = now_sec();

    std::printf("C++ move buffer checksum=%llu time=%.6f sec\n",
                static_cast<unsigned long long>(move_checksum), t1 - t0);
    std::printf("C++ copy buffer checksum=%llu time=%.6f sec\n",
                static_cast<unsigned long long>(copy_checksum), t2 - t1);
    return 0;
}
