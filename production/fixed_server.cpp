#define FIXED_MAIN fixed_single_main
#include "fixed.cpp"
#undef FIXED_MAIN

int main(int argc, char **argv) {
    if (argc != 3) {
        std::cerr << "usage: fixed_server N K\n";
        return 2;
    }
    std::string id, r, x, y, z;
    while (std::cin >> id >> r >> x >> y >> z) {
        std::vector<std::string> arguments{argv[0], argv[1], argv[2], r, x, y, z};
        std::vector<char *> pointers;
        for (std::string &argument : arguments) pointers.push_back(argument.data());
        int code = 2;
        try {
            code = fixed_single_main(static_cast<int>(pointers.size()), pointers.data());
        } catch (const std::exception &error) {
            std::cerr << "fixed server exception: " << error.what() << '\n';
        }
        std::cout.flush();
        std::cerr.flush();
        std::cerr << "JOB_END " << id << " code=" << code << '\n';
        std::cerr.flush();
    }
    return std::cin.eof() ? 0 : 2;
}
