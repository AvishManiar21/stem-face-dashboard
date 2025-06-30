#!/usr/bin/env python3
"""
Test script to verify that Jinja2 has been completely removed
and the application works with static HTML and JavaScript.
"""

import os
import re

def test_no_jinja_in_templates():
    """Test that no Jinja2 syntax exists in HTML templates"""
    print("🔍 Testing for Jinja2 syntax in templates...")
    
    jinja_patterns = [
        r'\{\{.*?\}\}',  # {{ variable }}
        r'\{%.*?%\}',    # {% if/for/block %}
        r'\{#.*?#\}',    # {# comment #}
    ]
    
    template_dir = 'templates'
    jinja_found = False
    
    for filename in os.listdir(template_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(template_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in jinja_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"❌ Found Jinja2 syntax in {filename}:")
                    for match in matches[:3]:  # Show first 3 matches
                        print(f"   {match}")
                    jinja_found = True
    
    if not jinja_found:
        print("✅ No Jinja2 syntax found in templates")
    else:
        print("❌ Jinja2 syntax still present in templates")
    
    return not jinja_found

def test_no_render_template_imports():
    """Test that no render_template imports exist in Python files"""
    print("\n🔍 Testing for render_template imports...")
    
    python_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'test_no_jinja.py']
    render_template_found = False
    
    for filename in python_files:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'render_template' in content:
            print(f"❌ Found render_template in {filename}")
            render_template_found = True
    
    if not render_template_found:
        print("✅ No render_template imports found")
    else:
        print("❌ render_template still present in Python files")
    
    return not render_template_found

def test_static_html_serving():
    """Test that HTML files are served statically"""
    print("\n🔍 Testing static HTML serving...")
    
    template_dir = 'templates'
    html_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    
    for filename in html_files:
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for JavaScript API calls (more flexible)
        if 'fetch(' in content:
            print(f"✅ {filename} contains API calls")
        elif filename == 'login.html':
            print(f"✅ {filename} is login form (no API calls needed)")
        else:
            print(f"⚠️  {filename} may not have API calls")

def test_api_endpoints_defined():
    """Test that API endpoints are defined in app.py"""
    print("\n🔍 Testing API endpoints...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    api_endpoints = [
        '/api/user-info',
        '/api/dashboard-data',
        '/api/calendar-data',
        '/api/upcoming-shifts',
        '/api/admin/users',
        '/api/admin/shifts',
        '/api/admin/audit-logs',
        '/api/chart-data'
    ]
    
    missing_endpoints = []
    for endpoint in api_endpoints:
        if f"@app.route('{endpoint}')" not in content:
            missing_endpoints.append(endpoint)
    
    if not missing_endpoints:
        print("✅ All expected API endpoints are defined")
    else:
        print("❌ Missing API endpoints:")
        for endpoint in missing_endpoints:
            print(f"   {endpoint}")
    
    return len(missing_endpoints) == 0

def test_javascript_functionality():
    """Test that JavaScript functions are present in templates"""
    print("\n🔍 Testing JavaScript functionality...")
    
    template_dir = 'templates'
    html_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    
    for filename in html_files:
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for common JavaScript patterns
        js_patterns = [
            'loadUserData()',
            'fetch(',
            'addEventListener',
            'DOMContentLoaded'
        ]
        
        found_patterns = []
        for pattern in js_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"✅ {filename} contains JavaScript: {', '.join(found_patterns)}")
        elif filename == 'login.html':
            print(f"✅ {filename} is login form (no JavaScript needed)")
        else:
            print(f"⚠️  {filename} may not have JavaScript functionality")

def test_template_structure():
    """Test that templates have proper structure without Jinja2"""
    print("\n🔍 Testing template structure...")
    
    template_dir = 'templates'
    html_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    
    for filename in html_files:
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for proper HTML structure
        if '<!DOCTYPE html>' in content and '<html' in content and '</html>' in content:
            print(f"✅ {filename} has proper HTML structure")
        else:
            print(f"❌ {filename} may have incomplete HTML structure")

def test_send_from_directory_usage():
    """Test that templates are served using send_from_directory"""
    print("\n🔍 Testing send_from_directory usage...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'send_from_directory' in content:
        print("✅ Templates are served using send_from_directory")
        return True
    else:
        print("❌ send_from_directory not found in app.py")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Jinja2 Removal and Static HTML Implementation")
    print("=" * 60)
    
    tests = [
        test_no_jinja_in_templates,
        test_no_render_template_imports,
        test_static_html_serving,
        test_api_endpoints_defined,
        test_javascript_functionality,
        test_template_structure,
        test_send_from_directory_usage
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Jinja2 has been successfully removed.")
        print("\n✅ The application now uses:")
        print("   - Static HTML templates")
        print("   - JavaScript API calls")
        print("   - No server-side templating")
        print("   - Clean separation of concerns")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main() 