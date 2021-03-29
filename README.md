# Multithread downloader
Simple tool that uses multiple threads to download a file. It pre-allocates space to the file before beginning, allowing the threads to write their own sections.

## Compilation
To compile, run
```
py -m pip install -r requirements.txt
py -m pip install -r requirements-build.txt
```

Then run
```
pyinstaller --onefile interface.py --additional-hooks-dir=hooks --noconsole
```

(Or run `compile.bat`, which executes the same `pyinstaller` command as written above.)

## Running without building
Simply run
```
py -m pip install -r requirements.txt
```

And then run
```
py interface.py
```
