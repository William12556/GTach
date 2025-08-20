============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/williamwatson/Documents/GitHub/GTach
plugins: anyio-4.9.0, cov-6.2.1, mock-3.14.1
collected 56 items

src/tests/provisioning/test_archive_manager.py ..............F.......    [ 39%]
src/tests/provisioning/test_config_processor.py ........FF.....          [ 66%]
src/tests/provisioning/test_package_creator.py F...FF......F......       [100%]

=================================== FAILURES ===================================
_________________ TestArchiveManager.test_should_exclude_file __________________

self = <provisioning.test_archive_manager.TestArchiveManager testMethod=test_should_exclude_file>

    def test_should_exclude_file(self):
        """Test file exclusion logic"""
        exclude_patterns = ['.DS_Store', '*.pyc', '__pycache__']
    
        test_cases = [
            (Path("file.py"), False),
            (Path("file.pyc"), True),
            (Path(".DS_Store"), True),
            (Path("some/__pycache__/file.py"), True),
            (Path("normal_file.txt"), False)
        ]
    
        for file_path, should_exclude in test_cases:
            result = self.manager._should_exclude_file(file_path, exclude_patterns)
>           self.assertEqual(result, should_exclude, f"Failed for {file_path}")
E           AssertionError: False != True : Failed for file.pyc

src/tests/provisioning/test_archive_manager.py:137: AssertionError
________________ TestConfigProcessor.test_process_json_template ________________

self = <provisioning.test_config_processor.TestConfigProcessor testMethod=test_process_json_template>

    def test_process_json_template(self):
        """Test JSON template processing"""
        template_file = self.template_dir / "app.template.json"
        output_file = self.output_dir / "app.json"
    
        variables = {
            'app_dir': '/opt/gtach',
            'user': 'pi',
            'performance_profile': 'embedded',
            'fps_limit': 30,
            'platform_name': 'raspberry-pi',
            'gpio_available': True
        }
    
        self.processor._process_json_template(template_file, output_file, variables)
    
        self.assertTrue(output_file.exists())
    
        # Parse and verify JSON
        with open(output_file) as f:
>           data = json.load(f)

src/tests/provisioning/test_config_processor.py:265: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/json/__init__.py:293: in load
    return loads(fp.read(),
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <json.decoder.JSONDecoder object at 0x102f92b50>
s = '{\n  "application": {\n    "name": "GTach",\n    "version": "1.0.0",\n    "install_dir": "/opt/gtach",\n    "user": "...ofile": "embedded",\n    "fps_limit": 30\n  },\n  "platform": {\n    "name": "raspberry-pi",\n    "gpio": True\n  }\n}'
idx = 0

    def raw_decode(self, s, idx=0):
        """Decode a JSON document from ``s`` (a ``str`` beginning with
        a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
    
        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.
    
        """
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration as err:
>           raise JSONDecodeError("Expecting value", s, err.value) from None
E           json.decoder.JSONDecodeError: Expecting value: line 14 column 13 (char 248)

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/json/decoder.py:355: JSONDecodeError
------------------------------ Captured log call -------------------------------
ERROR    provisioning.config_processor.ConfigProcessor:config_processor.py:530 JSON processing error in /var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpw2lntbxi/test_project/templates/app.template.json: Expecting value: line 14 column 13 (char 248)
__________________ TestConfigProcessor.test_process_templates __________________

self = <provisioning.test_config_processor.TestConfigProcessor testMethod=test_process_templates>
mock_config_manager = <MagicMock name='ConfigManager' id='4384801408'>

    @patch('provisioning.config_processor.ConfigManager')
    def test_process_templates(self, mock_config_manager):
        """Test complete template processing"""
        # Mock configuration
        mock_config = Mock()
        mock_config.port = "AUTO"
        mock_config.baudrate = 38400
        mock_config.bluetooth.scan_duration = 8.0
        mock_config.bluetooth.timeout = 2.0
        mock_config.display.fps_limit = 60
        mock_config.display.mode = "DIGITAL"
        mock_config.debug_logging = False
    
        mock_config_manager.return_value.load_config.return_value = mock_config
    
        # Process all templates
        processed_files = self.processor.process_templates(
            self.template_dir,
            self.output_dir
        )
    
        # Should have processed all template files
        self.assertTrue(len(processed_files) > 0)
    
        # Check specific files were created
        expected_files = ['config.yaml', 'gtach.service', 'environment']
    
        for expected_file in expected_files:
            file_path = self.output_dir / expected_file
>           self.assertTrue(file_path.exists(), f"Expected file not created: {expected_file}")
E           AssertionError: False is not true : Expected file not created: environment

src/tests/provisioning/test_config_processor.py:327: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    provisioning.config_processor.ConfigProcessor:config_processor.py:530 JSON processing error in /var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmps3z7nhhh/test_project/templates/app.template.json: Expecting value: line 14 column 13 (char 252)
WARNING  provisioning.config_processor.ConfigProcessor:config_processor.py:629 Bluetooth timeout below platform minimum: 5.0
_______________ TestPackageCreator.test_auto_detect_project_root _______________

self = <provisioning.test_package_creator.TestPackageCreator testMethod=test_auto_detect_project_root>

    def test_auto_detect_project_root(self):
        """Test auto-detection of project root"""
        # Create nested directory structure
        nested_dir = self.project_root / "deep" / "nested" / "path"
        nested_dir.mkdir(parents=True)
    
        # Initialize from nested directory
        original_cwd = os.getcwd()
        try:
            os.chdir(nested_dir)
            creator = PackageCreator()
>           self.assertEqual(creator.project_root, self.project_root)
E           AssertionError: PosixPath('/Users/williamwatson/Documents/GitHub/GTach') != PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f000[28 chars]ect')

src/tests/provisioning/test_package_creator.py:113: AssertionError
_________________ TestPackageCreator.test_create_package_basic _________________

s = b'\xf1e\xdcYg.U,'

    def nti(s):
        """Convert a number field to a python number.
        """
        # There are two possible encodings for a number field, see
        # itn() below.
        if s[0] in (0o200, 0o377):
            n = 0
            for i in range(len(s) - 1):
                n <<= 8
                n += s[i + 1]
            if s[0] == 0o377:
                n = -(256 ** (len(s) - 1) - n)
        else:
            try:
>               s = nts(s, "ascii", "strict")

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:186: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

s = b'\xf1e\xdcYg.U,', encoding = 'ascii', errors = 'strict'

    def nts(s, encoding, errors):
        """Convert a null-terminated bytes object to a string.
        """
        p = s.find(b"\0")
        if p != -1:
            s = s[:p]
>       return s.decode(encoding, errors)
E       UnicodeDecodeError: 'ascii' codec can't decode byte 0xf1 in position 0: ordinal not in range(128)

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:170: UnicodeDecodeError

During handling of the above exception, another exception occurred:

self = <tarfile.TarFile object at 0x1055a39a0>
name = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output/test-package-1.0.0-20250806_113259.tar.gz')
mode = 'a'
fileobj = <_io.BufferedRandom name='/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output/test-package-1.0.0-20250806_113259.tar.gz'>
format = None, tarinfo = None, dereference = None, ignore_zeros = None
encoding = None, errors = 'surrogateescape', pax_headers = None, debug = None
errorlevel = None, copybufsize = None

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None,
            errorlevel=None, copybufsize=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]
    
        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj
    
        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors
    
        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}
    
        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel
    
        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []       # list of members as TarInfo objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
    
        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()
    
            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
>                       tarinfo = self.tarinfo.fromtarfile(self)

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1560: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1117: in fromtarfile
    obj = cls.frombuf(buf, tarfile.encoding, tarfile.errors)
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1059: in frombuf
    chksum = nti(buf[148:156])
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

s = b'\xf1e\xdcYg.U,'

    def nti(s):
        """Convert a number field to a python number.
        """
        # There are two possible encodings for a number field, see
        # itn() below.
        if s[0] in (0o200, 0o377):
            n = 0
            for i in range(len(s) - 1):
                n <<= 8
                n += s[i + 1]
            if s[0] == 0o377:
                n = -(256 ** (len(s) - 1) - n)
        else:
            try:
                s = nts(s, "ascii", "strict")
                n = int(s.strip() or "0", 8)
            except ValueError:
>               raise InvalidHeaderError("invalid header")
E               tarfile.InvalidHeaderError: invalid header

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:189: InvalidHeaderError

During handling of the above exception, another exception occurred:

self = <provisioning.package_creator.PackageCreator object at 0x1055ae640>
package_config = PackageConfig(package_name='test-package', version='1.0.0', target_platform='raspberry-pi', source_dirs=['src/obdii'],...folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output', include_dependencies=True, create_install_script=True)
output_path = None

    def create_package(self,
                      package_config: Optional[PackageConfig] = None,
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create deployment package with thread-safe operations.
    
        Args:
            package_config: Package configuration. Uses default if None.
            output_path: Output file path. Auto-generated if None.
    
        Returns:
            Path to created package file
    
        Raises:
            RuntimeError: If package creation fails
            ValueError: If configuration is invalid
        """
        with self._creation_lock:
            self._increment_operation_count()
    
            config = package_config or self.default_config
            start_time = time.perf_counter()
    
            self.logger.info(f"Starting package creation: {config.package_name} v{config.version}")
    
            try:
                # Validate configuration
                self._validate_config(config)
    
                # Setup workspace
                with self._setup_workspace() as workspace:
                    self.workspace_dir = workspace
    
                    # Collect source files
                    source_files = self._collect_source_files(config)
                    self.logger.debug(f"Collected {len(source_files)} source files")
    
                    # Copy files to workspace
                    self._copy_files_to_workspace(source_files, config)
    
                    # Process configuration templates
                    template_files = self._process_config_templates(config)
    
                    # Generate installation scripts
                    script_files = self._generate_install_scripts(config)
    
                    # Create package manifest
                    manifest = self._create_manifest(
                        config, source_files, template_files, script_files
                    )
    
                    # Create archive
>                   package_path = self._create_archive(config, manifest, output_path)

src/provisioning/package_creator.py:242: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/provisioning/package_creator.py:702: in _create_archive
    self._update_manifest_in_archive(archive_path, manifest)
src/provisioning/package_creator.py:742: in _update_manifest_in_archive
    with tarfile.open(archive_path, 'a') as tar:
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1679: in open
    return cls.taropen(name, mode, fileobj, **kwargs)
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1689: in taropen
    return cls(name, mode, fileobj, **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tarfile.TarFile object at 0x1055a39a0>
name = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output/test-package-1.0.0-20250806_113259.tar.gz')
mode = 'a'
fileobj = <_io.BufferedRandom name='/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output/test-package-1.0.0-20250806_113259.tar.gz'>
format = None, tarinfo = None, dereference = None, ignore_zeros = None
encoding = None, errors = 'surrogateescape', pax_headers = None, debug = None
errorlevel = None, copybufsize = None

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None,
            errorlevel=None, copybufsize=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]
    
        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj
    
        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors
    
        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}
    
        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel
    
        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []       # list of members as TarInfo objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
    
        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()
    
            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
>                       raise ReadError(str(e))
E                       tarfile.ReadError: invalid header

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1566: ReadError

The above exception was the direct cause of the following exception:

self = <provisioning.test_package_creator.TestPackageCreator testMethod=test_create_package_basic>
mock_config_processor_class = <MagicMock name='ConfigProcessor' id='4384809888'>

    @patch('provisioning.config_processor.ConfigProcessor')
    def test_create_package_basic(self, mock_config_processor_class):
        """Test basic package creation"""
        # Mock the config processor to avoid template processing issues
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
    
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            config_template_dirs=[],  # Empty to skip template processing
            output_dir=str(self.output_dir),
            verify_integrity=False  # Skip integrity check for speed
        )
    
>       package_path = self.creator.create_package(config)

src/tests/provisioning/test_package_creator.py:264: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <provisioning.package_creator.PackageCreator object at 0x1055ae640>
package_config = PackageConfig(package_name='test-package', version='1.0.0', target_platform='raspberry-pi', source_dirs=['src/obdii'],...folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpotsg5j26/output', include_dependencies=True, create_install_script=True)
output_path = None

    def create_package(self,
                      package_config: Optional[PackageConfig] = None,
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create deployment package with thread-safe operations.
    
        Args:
            package_config: Package configuration. Uses default if None.
            output_path: Output file path. Auto-generated if None.
    
        Returns:
            Path to created package file
    
        Raises:
            RuntimeError: If package creation fails
            ValueError: If configuration is invalid
        """
        with self._creation_lock:
            self._increment_operation_count()
    
            config = package_config or self.default_config
            start_time = time.perf_counter()
    
            self.logger.info(f"Starting package creation: {config.package_name} v{config.version}")
    
            try:
                # Validate configuration
                self._validate_config(config)
    
                # Setup workspace
                with self._setup_workspace() as workspace:
                    self.workspace_dir = workspace
    
                    # Collect source files
                    source_files = self._collect_source_files(config)
                    self.logger.debug(f"Collected {len(source_files)} source files")
    
                    # Copy files to workspace
                    self._copy_files_to_workspace(source_files, config)
    
                    # Process configuration templates
                    template_files = self._process_config_templates(config)
    
                    # Generate installation scripts
                    script_files = self._generate_install_scripts(config)
    
                    # Create package manifest
                    manifest = self._create_manifest(
                        config, source_files, template_files, script_files
                    )
    
                    # Create archive
                    package_path = self._create_archive(config, manifest, output_path)
    
                    # Verify integrity
                    if config.verify_integrity:
                        self._verify_package_integrity(package_path, manifest)
    
                    elapsed = time.perf_counter() - start_time
                    self.logger.info(
                        f"Package created successfully: {package_path} ({elapsed:.2f}s)"
                    )
    
                    return package_path
    
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Package creation failed after {elapsed:.2f}s: {e}")
>               raise RuntimeError(f"Package creation failed: {e}") from e
E               RuntimeError: Package creation failed: invalid header

src/provisioning/package_creator.py:258: RuntimeError
------------------------------ Captured log call -------------------------------
ERROR    provisioning.package_creator.PackageCreator:package_creator.py:257 Package creation failed after 0.00s: invalid header
___________ TestPackageCreator.test_create_package_with_output_path ____________

s = b'\xf1\xa2;\xe8\xf7z\x03\x7f'

    def nti(s):
        """Convert a number field to a python number.
        """
        # There are two possible encodings for a number field, see
        # itn() below.
        if s[0] in (0o200, 0o377):
            n = 0
            for i in range(len(s) - 1):
                n <<= 8
                n += s[i + 1]
            if s[0] == 0o377:
                n = -(256 ** (len(s) - 1) - n)
        else:
            try:
>               s = nts(s, "ascii", "strict")

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:186: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

s = b'\xf1\xa2;\xe8\xf7z\x03\x7f', encoding = 'ascii', errors = 'strict'

    def nts(s, encoding, errors):
        """Convert a null-terminated bytes object to a string.
        """
        p = s.find(b"\0")
        if p != -1:
            s = s[:p]
>       return s.decode(encoding, errors)
E       UnicodeDecodeError: 'ascii' codec can't decode byte 0xf1 in position 0: ordinal not in range(128)

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:170: UnicodeDecodeError

During handling of the above exception, another exception occurred:

self = <tarfile.TarFile object at 0x10558bcd0>
name = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz')
mode = 'a'
fileobj = <_io.BufferedRandom name='/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz'>
format = None, tarinfo = None, dereference = None, ignore_zeros = None
encoding = None, errors = 'surrogateescape', pax_headers = None, debug = None
errorlevel = None, copybufsize = None

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None,
            errorlevel=None, copybufsize=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]
    
        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj
    
        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors
    
        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}
    
        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel
    
        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []       # list of members as TarInfo objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
    
        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()
    
            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
>                       tarinfo = self.tarinfo.fromtarfile(self)

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1560: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1117: in fromtarfile
    obj = cls.frombuf(buf, tarfile.encoding, tarfile.errors)
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1059: in frombuf
    chksum = nti(buf[148:156])
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

s = b'\xf1\xa2;\xe8\xf7z\x03\x7f'

    def nti(s):
        """Convert a number field to a python number.
        """
        # There are two possible encodings for a number field, see
        # itn() below.
        if s[0] in (0o200, 0o377):
            n = 0
            for i in range(len(s) - 1):
                n <<= 8
                n += s[i + 1]
            if s[0] == 0o377:
                n = -(256 ** (len(s) - 1) - n)
        else:
            try:
                s = nts(s, "ascii", "strict")
                n = int(s.strip() or "0", 8)
            except ValueError:
>               raise InvalidHeaderError("invalid header")
E               tarfile.InvalidHeaderError: invalid header

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:189: InvalidHeaderError

During handling of the above exception, another exception occurred:

self = <provisioning.package_creator.PackageCreator object at 0x1055dbbe0>
package_config = PackageConfig(package_name='test-package', version='1.0.0', target_platform='raspberry-pi', source_dirs=['src/obdii'],...eserve_permissions=True, verify_integrity=True, output_dir=None, include_dependencies=True, create_install_script=True)
output_path = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz')

    def create_package(self,
                      package_config: Optional[PackageConfig] = None,
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create deployment package with thread-safe operations.
    
        Args:
            package_config: Package configuration. Uses default if None.
            output_path: Output file path. Auto-generated if None.
    
        Returns:
            Path to created package file
    
        Raises:
            RuntimeError: If package creation fails
            ValueError: If configuration is invalid
        """
        with self._creation_lock:
            self._increment_operation_count()
    
            config = package_config or self.default_config
            start_time = time.perf_counter()
    
            self.logger.info(f"Starting package creation: {config.package_name} v{config.version}")
    
            try:
                # Validate configuration
                self._validate_config(config)
    
                # Setup workspace
                with self._setup_workspace() as workspace:
                    self.workspace_dir = workspace
    
                    # Collect source files
                    source_files = self._collect_source_files(config)
                    self.logger.debug(f"Collected {len(source_files)} source files")
    
                    # Copy files to workspace
                    self._copy_files_to_workspace(source_files, config)
    
                    # Process configuration templates
                    template_files = self._process_config_templates(config)
    
                    # Generate installation scripts
                    script_files = self._generate_install_scripts(config)
    
                    # Create package manifest
                    manifest = self._create_manifest(
                        config, source_files, template_files, script_files
                    )
    
                    # Create archive
>                   package_path = self._create_archive(config, manifest, output_path)

src/provisioning/package_creator.py:242: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/provisioning/package_creator.py:702: in _create_archive
    self._update_manifest_in_archive(archive_path, manifest)
src/provisioning/package_creator.py:742: in _update_manifest_in_archive
    with tarfile.open(archive_path, 'a') as tar:
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1679: in open
    return cls.taropen(name, mode, fileobj, **kwargs)
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1689: in taropen
    return cls(name, mode, fileobj, **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tarfile.TarFile object at 0x10558bcd0>
name = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz')
mode = 'a'
fileobj = <_io.BufferedRandom name='/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz'>
format = None, tarinfo = None, dereference = None, ignore_zeros = None
encoding = None, errors = 'surrogateescape', pax_headers = None, debug = None
errorlevel = None, copybufsize = None

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None,
            errorlevel=None, copybufsize=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]
    
        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj
    
        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors
    
        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}
    
        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel
    
        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []       # list of members as TarInfo objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
    
        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()
    
            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
>                       raise ReadError(str(e))
E                       tarfile.ReadError: invalid header

/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/tarfile.py:1566: ReadError

The above exception was the direct cause of the following exception:

self = <provisioning.test_package_creator.TestPackageCreator testMethod=test_create_package_with_output_path>
mock_config_processor_class = <MagicMock name='ConfigProcessor' id='4384994688'>

    @patch('provisioning.config_processor.ConfigProcessor')
    def test_create_package_with_output_path(self, mock_config_processor_class):
        """Test package creation with specific output path"""
        # Mock the config processor
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
    
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            config_template_dirs=[]  # Empty to skip template processing
        )
    
        output_path = self.output_dir / "custom-package.tar.gz"
>       package_path = self.creator.create_package(config, output_path)

src/tests/provisioning/test_package_creator.py:290: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <provisioning.package_creator.PackageCreator object at 0x1055dbbe0>
package_config = PackageConfig(package_name='test-package', version='1.0.0', target_platform='raspberry-pi', source_dirs=['src/obdii'],...eserve_permissions=True, verify_integrity=True, output_dir=None, include_dependencies=True, create_install_script=True)
output_path = PosixPath('/var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmpavqvdjzr/output/custom-package.tar.gz')

    def create_package(self,
                      package_config: Optional[PackageConfig] = None,
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create deployment package with thread-safe operations.
    
        Args:
            package_config: Package configuration. Uses default if None.
            output_path: Output file path. Auto-generated if None.
    
        Returns:
            Path to created package file
    
        Raises:
            RuntimeError: If package creation fails
            ValueError: If configuration is invalid
        """
        with self._creation_lock:
            self._increment_operation_count()
    
            config = package_config or self.default_config
            start_time = time.perf_counter()
    
            self.logger.info(f"Starting package creation: {config.package_name} v{config.version}")
    
            try:
                # Validate configuration
                self._validate_config(config)
    
                # Setup workspace
                with self._setup_workspace() as workspace:
                    self.workspace_dir = workspace
    
                    # Collect source files
                    source_files = self._collect_source_files(config)
                    self.logger.debug(f"Collected {len(source_files)} source files")
    
                    # Copy files to workspace
                    self._copy_files_to_workspace(source_files, config)
    
                    # Process configuration templates
                    template_files = self._process_config_templates(config)
    
                    # Generate installation scripts
                    script_files = self._generate_install_scripts(config)
    
                    # Create package manifest
                    manifest = self._create_manifest(
                        config, source_files, template_files, script_files
                    )
    
                    # Create archive
                    package_path = self._create_archive(config, manifest, output_path)
    
                    # Verify integrity
                    if config.verify_integrity:
                        self._verify_package_integrity(package_path, manifest)
    
                    elapsed = time.perf_counter() - start_time
                    self.logger.info(
                        f"Package created successfully: {package_path} ({elapsed:.2f}s)"
                    )
    
                    return package_path
    
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                self.logger.error(f"Package creation failed after {elapsed:.2f}s: {e}")
>               raise RuntimeError(f"Package creation failed: {e}") from e
E               RuntimeError: Package creation failed: invalid header

src/provisioning/package_creator.py:258: RuntimeError
------------------------------ Captured log call -------------------------------
ERROR    provisioning.package_creator.PackageCreator:package_creator.py:257 Package creation failed after 0.00s: invalid header
____________________ TestPackageCreator.test_thread_safety _____________________

self = <provisioning.test_package_creator.TestPackageCreator testMethod=test_thread_safety>
mock_config_processor_class = <MagicMock name='ConfigProcessor' id='4383782848'>

    @patch('provisioning.config_processor.ConfigProcessor')
    def test_thread_safety(self, mock_config_processor_class):
        """Test thread-safe package creation"""
        # Mock the config processor
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
    
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            config_template_dirs=[],  # Empty to skip template processing
            output_dir=str(self.output_dir),
            verify_integrity=False
        )
    
        results = []
        errors = []
    
        def create_package_thread(thread_id):
            try:
                output_path = self.output_dir / f"package-{thread_id}.tar.gz"
                package_path = self.creator.create_package(config, output_path)
                results.append(package_path)
            except Exception as e:
                errors.append(e)
    
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_package_thread, args=(i,))
            threads.append(thread)
            thread.start()
    
        # Wait for completion
        for thread in threads:
            thread.join()
    
        # Check results
>       self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
E       AssertionError: 3 != 0 : Errors occurred: [RuntimeError('Package creation failed: invalid header'), RuntimeError('Package creation failed: invalid header'), RuntimeError('Package creation failed: invalid header')]

src/tests/provisioning/test_package_creator.py:335: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    provisioning.package_creator.PackageCreator:package_creator.py:257 Package creation failed after 0.00s: invalid header
ERROR    provisioning.package_creator.PackageCreator:package_creator.py:257 Package creation failed after 0.00s: invalid header
ERROR    provisioning.package_creator.PackageCreator:package_creator.py:257 Package creation failed after 0.00s: invalid header
=============================== warnings summary ===============================
../../../Library/Python/3.9/lib/python/site-packages/pygame/pkgdata.py:25
  /Users/williamwatson/Library/Python/3.9/lib/python/site-packages/pygame/pkgdata.py:25: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    from pkg_resources import resource_stream, resource_exists

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED src/tests/provisioning/test_archive_manager.py::TestArchiveManager::test_should_exclude_file
FAILED src/tests/provisioning/test_config_processor.py::TestConfigProcessor::test_process_json_template
FAILED src/tests/provisioning/test_config_processor.py::TestConfigProcessor::test_process_templates
FAILED src/tests/provisioning/test_package_creator.py::TestPackageCreator::test_auto_detect_project_root
FAILED src/tests/provisioning/test_package_creator.py::TestPackageCreator::test_create_package_basic
FAILED src/tests/provisioning/test_package_creator.py::TestPackageCreator::test_create_package_with_output_path
FAILED src/tests/provisioning/test_package_creator.py::TestPackageCreator::test_thread_safety
=================== 7 failed, 49 passed, 1 warning in 0.42s ====================

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
