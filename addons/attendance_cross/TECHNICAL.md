# Biometric Attendance Integration - Technical Documentation

## Overview

This module provides integration between Odoo CE 18.0 and Biometric biometric devices for attendance management. The module structure is complete, but requires implementation of the actual Biometric ISAPI protocol calls.

## Module Structure

### Models

1. **biometric.device** - Stores device configuration (IP, port, credentials)
2. **attendance.log** - Stores attendance records downloaded from devices
3. **hr.employee** (extended) - Adds biometric_id and device assignment fields

### Wizards

1. **upload.employees.wizard** - Upload employees to Biometric devices
2. **download.attendance.wizard** - Download attendance records from devices
3. **attendance.report.wizard** - Generate Excel attendance reports

### Views

- Device management interface
- Attendance log browser
- Employee integration fields
- Wizard forms for operations

## Biometric API Implementation Required

The module includes placeholder methods that need actual Biometric ISAPI implementation:

### 1. Device Connection Test (`biometric_device.py:test_connection`)

```python
def test_connection(self):
    import requests
    from requests.auth import HTTPDigestAuth
    
    url = f'http://{self.ip_address}:{self.port}/ISAPI/System/deviceInfo'
    try:
        response = requests.get(url, auth=HTTPDigestAuth(self.username, self.password), timeout=10)
        if response.status_code == 200:
            self.connection_status = 'connected'
        else:
            self.connection_status = 'failed'
    except Exception as e:
        self.connection_status = 'failed'
        raise UserError(_('Connection failed: %s') % str(e))
```

### 2. Employee Upload (`biometric_device.py:upload_employee`)

```python
def upload_employee(self, employee):
    # Biometric ISAPI endpoint for adding users
    # POST to /ISAPI/AccessControl/UserInfo/Record
    # XML payload with user details
    import requests
    from requests.auth import HTTPDigestAuth
    
    url = f'http://{self.ip_address}:{self.port}/ISAPI/AccessControl/UserInfo/Record'
    
    xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<UserInfo>
    <employeeNo>{employee.biometric_id}</employeeNo>
    <name>{employee.name}</name>
    <userType>normal</userType>
    <Valid>
        <enable>true</enable>
        <beginTime>2024-01-01T00:00:00</beginTime>
        <endTime>2030-12-31T23:59:59</endTime>
    </Valid>
</UserInfo>"""
    
    response = requests.post(url, data=xml_payload, 
                           auth=HTTPDigestAuth(self.username, self.password),
                           headers={'Content-Type': 'application/xml'})
    
    if response.status_code == 200:
        employee.biometric_uploaded = True
    else:
        raise UserError(_('Upload failed: %s') % response.text)
```

### 3. Attendance Download (`biometric_device.py:download_attendance`)

```python
def download_attendance(self, start_date, end_date):
    # Biometric ISAPI endpoint for attendance records
    # POST to /ISAPI/AccessControl/AcsEvent?format=json
    # JSON payload with date range
    
    import requests
    from requests.auth import HTTPDigestAuth
    import json
    
    url = f'http://{self.ip_address}:{self.port}/ISAPI/AccessControl/AcsEvent?format=json'
    
    json_payload = {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 1000,
            "major": 5,  # Attendance events
            "minor": 0,
            "startTime": start_date.strftime('%Y-%m-%dT%H:%M:%S'),
            "endTime": end_date.strftime('%Y-%m-%dT%H:%M:%S'),
            "doorNum": 1
        }
    }
    
    response = requests.post(url, json=json_payload,
                           auth=HTTPDigestAuth(self.username, self.password))
    
    if response.status_code == 200:
        data = response.json()
        # Parse response and create attendance.log records
        for event in data.get('AcsEvent', []):
            self._create_attendance_log(event)
    else:
        raise UserError(_('Download failed: %s') % response.text)
```

## Dependencies

1. **Python packages:**
   - `requests` - For HTTP calls to Biometric devices
   - `openpyxl` - For Excel report generation (already in requirements)
   - `xml.etree.ElementTree` - For XML parsing (standard library)

2. **Odoo dependencies:**
   - `base`
   - `hr`
   - `hr_attendance`
   - `web`
   - `report_xlsx`

## Configuration Steps

1. Install the module in Odoo CE 18.0
2. Add `requests` to your Odoo Python environment:
   ```bash
   pip install requests
   ```
3. Configure Biometric devices in Odoo:
   - Go to Attendance → Biometric Devices
   - Add device with IP, port, username, password
   - Test connection
4. Assign devices to employees in HR module
5. Upload employees to devices
6. Download attendance records
7. Generate reports

## Security Considerations

1. **Device credentials:** Stored encrypted in Odoo database
2. **Network security:** Ensure Odoo server can reach Biometric devices on network
3. **API permissions:** Biometric devices should have appropriate user permissions
4. **Data privacy:** Attendance logs contain sensitive employee data

## Testing

1. Unit tests should be written for:
   - Device connection testing
   - Attendance log processing
   - Report generation
2. Integration tests with mock Biometric API
3. Manual testing with actual devices

## Troubleshooting

1. **Connection failures:** Check network connectivity, firewall, credentials
2. **Upload failures:** Verify employee biometric_id is unique
3. **Download failures:** Check date ranges and device time settings
4. **Report generation failures:** Ensure openpyxl is installed

## Extensions

Potential future enhancements:

1. Real-time attendance sync via WebSocket
2. Facial recognition photo sync
3. Multiple device types support
4. Advanced reporting with analytics
5. Mobile app integration

## References

1. Biometric ISAPI Developer Guide
2. Odoo ORM Documentation
3. Python requests library documentation