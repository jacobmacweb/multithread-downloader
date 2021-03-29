# Multithread downloader
Simple tool that uses multiple threads to download a file. It pre-allocates space to the file before beginning, allowing the threads to write their own sections.

## Compilation
To compile, run
```
py -m pip install -r requirements.txt
py -m pip install -r requirements-build.txt
```

And then run `compile.bat`, or copy the contents of the file and run it in your console. The file is there for simplicity, and nothing more.

## Running without building
Simply run
```
py -m pip install -r requirements.txt
```

And then run
```
py interface.py
```
