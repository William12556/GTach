============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/williamwatson/Documents/GitHub/GTach
plugins: anyio-4.9.0, cov-6.2.1, mock-3.14.1
collected 56 items

src/tests/provisioning/test_archive_manager.py ..............F.......    [ 39%]
src/tests/provisioning/test_config_processor.py ........FF.....          [ 66%]
src/tests/provisioning/test_package_creator.py F..................       [100%]

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

self = <json.decoder.JSONDecoder object at 0x105b32b50>
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
ERROR    provisioning.config_processor.ConfigProcessor:config_processor.py:530 JSON processing error in /var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmp62l7bkgq/test_project/templates/app.template.json: Expecting value: line 14 column 13 (char 248)
__________________ TestConfigProcessor.test_process_templates __________________

self = <provisioning.test_config_processor.TestConfigProcessor testMethod=test_process_templates>
mock_config_manager = <MagicMock name='ConfigManager' id='4429751344'>

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
ERROR    provisioning.config_processor.ConfigProcessor:config_processor.py:530 JSON processing error in /var/folders/vf/pcx_n9lx72v5q7kcnhcb34f00000gn/T/tmp4hexc8lx/test_project/templates/app.template.json: Expecting value: line 14 column 13 (char 252)
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
=================== 4 failed, 52 passed, 1 warning in 0.27s ====================

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
