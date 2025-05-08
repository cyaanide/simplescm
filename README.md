## simplescm - a suite of compiler + vm for scheme

### Compiler

The compiler converts scheme code into a custom bytecode. To generate the bytecode: 

`python3 ./compiler.py -i <input_file> -o <output_file>`

### VM

To build and run the VM:

* Create a directory called `build`
* `cd` into the VM folder and run the command `cmake -S . -B ../build`
* `cd` into the build folder and run the command `cmake --build .`
* This should create an executable called `vm` . Can run this executable by running the command `./vm <compiled_file>`
* To run the VM in debugging mode, provide the `-d` flag

