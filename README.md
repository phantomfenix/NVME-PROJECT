# SSD FIRMWARE DESIGN AND VALIDATION / UDG - SOLIDIGM
  Final Project - NVME Module
  - Test Manager [Confirmed]
  - Test 1 [Test 1: ID-CTRL]
     - Add admin_passthru_logger
  - Test 2 [Test 2: SMART-LOG]
     - Add admin_passthru_logger
  - Test 3 [Test 3: ID-NS]
      - Add admin_passthru_logger

############################################################

project_root/
├── test_suite_runner.py #Wrapper
├── test_manager.py
└── tests/
    ├── __init__.py
    ├── admin_passthru_test.py
    ├── example_test_1.py
    ├── example_test_2.py
    ├── example_test_3.py
 
