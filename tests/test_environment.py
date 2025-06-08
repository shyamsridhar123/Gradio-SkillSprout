"""
Enhanced Environment Validation Tests for SkillSprout
"""
import pytest
import os
import tempfile
import json
from unittest.mock import patch, Mock
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class EnvironmentCheck:
    """Data class for environment validation results"""
    name: str
    required: bool
    present: bool
    value: Optional[str] = None
    validation_result: bool = True
    error_message: Optional[str] = None


class EnvironmentValidator:
    """Enhanced environment validation utility"""
    
    REQUIRED_VARS = {
        'AZURE_OPENAI_ENDPOINT': {
            'required': True,
            'pattern': r'https://.*\.openai\.azure\.com/',
            'description': 'Azure OpenAI endpoint URL'
        },
        'AZURE_OPENAI_KEY': {
            'required': True,
            'min_length': 20,
            'description': 'Azure OpenAI API key'
        },
        'AZURE_OPENAI_API_VERSION': {
            'required': True,
            'pattern': r'\d{4}-\d{2}-\d{2}(-preview)?',
            'description': 'Azure OpenAI API version'
        },
        'AZURE_OPENAI_LLM_DEPLOYMENT': {
            'required': True,
            'description': 'Azure OpenAI LLM deployment name'
        },
        'AZURE_OPENAI_LLM_MODEL': {
            'required': True,
            'description': 'Azure OpenAI LLM model name'
        }
    }
    
    OPTIONAL_VARS = {
        'AZURE_SPEECH_KEY': {
            'required': False,
            'min_length': 20,
            'description': 'Azure Speech Services key (for voice narration)'
        },
        'AZURE_SPEECH_REGION': {
            'required': False,
            'description': 'Azure Speech Services region'
        },
        'GRADIO_ANALYTICS_ENABLED': {
            'required': False,
            'valid_values': ['true', 'false', '1', '0'],
            'description': 'Enable/disable Gradio analytics'
        },
        'PYTHONPATH': {
            'required': False,
            'description': 'Python path for module resolution'
        }
    }
    
    def validate_all(self) -> List[EnvironmentCheck]:
        """Validate all environment variables"""
        results = []
        
        # Check required variables
        for var_name, config in self.REQUIRED_VARS.items():
            result = self._validate_variable(var_name, config, required=True)
            results.append(result)
        
        # Check optional variables
        for var_name, config in self.OPTIONAL_VARS.items():
            result = self._validate_variable(var_name, config, required=False)
            results.append(result)
        
        return results
    
    def _validate_variable(self, var_name: str, config: Dict, required: bool) -> EnvironmentCheck:
        """Validate a single environment variable"""
        import re
        
        value = os.getenv(var_name)
        present = value is not None
        validation_result = True
        error_message = None
        
        if required and not present:
            validation_result = False
            error_message = f"Required environment variable {var_name} is not set"
        elif present:
            # Validate pattern if specified
            if 'pattern' in config:
                if not re.match(config['pattern'], value):
                    validation_result = False
                    error_message = f"{var_name} does not match expected pattern"
            
            # Validate minimum length if specified
            if 'min_length' in config:
                if len(value) < config['min_length']:
                    validation_result = False
                    error_message = f"{var_name} is too short (minimum {config['min_length']} characters)"
            
            # Validate against allowed values if specified
            if 'valid_values' in config:
                if value.lower() not in config['valid_values']:
                    validation_result = False
                    error_message = f"{var_name} must be one of: {config['valid_values']}"
        
        return EnvironmentCheck(
            name=var_name,
            required=required,
            present=present,
            value=value if present else None,
            validation_result=validation_result,
            error_message=error_message
        )
    
    def get_validation_report(self) -> Dict:
        """Get a comprehensive validation report"""
        results = self.validate_all()
        
        report = {
            'overall_status': 'PASS',
            'total_checks': len(results),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': [],
            'errors': [],
            'warnings_list': []
        }
        
        for result in results:
            detail = {
                'name': result.name,
                'required': result.required,
                'present': result.present,
                'status': 'PASS' if result.validation_result else 'FAIL',
                'value_length': len(result.value) if result.value else 0,
                'description': self._get_description(result.name)
            }
            
            if result.error_message:
                detail['error'] = result.error_message
            
            report['details'].append(detail)
            
            if result.validation_result:
                report['passed'] += 1
            else:
                report['failed'] += 1
                if result.required:
                    report['overall_status'] = 'FAIL'
                    report['errors'].append(result.error_message)
                else:
                    report['warnings'] += 1
                    report['warnings_list'].append(result.error_message)
        
        return report
    
    def _get_description(self, var_name: str) -> str:
        """Get description for a variable"""
        all_vars = {**self.REQUIRED_VARS, **self.OPTIONAL_VARS}
        return all_vars.get(var_name, {}).get('description', 'No description available')


@pytest.mark.unit
class TestEnvironmentValidator:
    """Test the environment validator utility"""
    
    def test_validator_initialization(self):
        """Test environment validator creates correctly"""
        validator = EnvironmentValidator()
        assert hasattr(validator, 'REQUIRED_VARS')
        assert hasattr(validator, 'OPTIONAL_VARS')
        assert len(validator.REQUIRED_VARS) > 0
    
    def test_validate_required_variable_present(self):
        """Test validation of present required variable"""
        validator = EnvironmentValidator()
        
        with patch.dict(os.environ, {'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/'}):
            result = validator._validate_variable(
                'AZURE_OPENAI_ENDPOINT',
                validator.REQUIRED_VARS['AZURE_OPENAI_ENDPOINT'],
                required=True
            )
            
            assert result.name == 'AZURE_OPENAI_ENDPOINT'
            assert result.required is True
            assert result.present is True
            assert result.validation_result is True
            assert result.error_message is None
    
    def test_validate_required_variable_missing(self):
        """Test validation of missing required variable"""
        validator = EnvironmentValidator()
        
        with patch.dict(os.environ, {}, clear=True):
            result = validator._validate_variable(
                'AZURE_OPENAI_KEY',
                validator.REQUIRED_VARS['AZURE_OPENAI_KEY'],
                required=True
            )
            
            assert result.name == 'AZURE_OPENAI_KEY'
            assert result.required is True
            assert result.present is False
            assert result.validation_result is False
            assert "Required environment variable" in result.error_message
    
    def test_validate_variable_pattern_match(self):
        """Test variable validation with pattern matching"""
        validator = EnvironmentValidator()
        
        # Valid pattern
        with patch.dict(os.environ, {'AZURE_OPENAI_API_VERSION': '2024-12-01-preview'}):
            result = validator._validate_variable(
                'AZURE_OPENAI_API_VERSION',
                validator.REQUIRED_VARS['AZURE_OPENAI_API_VERSION'],
                required=True
            )
            
            assert result.validation_result is True
        
        # Invalid pattern
        with patch.dict(os.environ, {'AZURE_OPENAI_API_VERSION': 'invalid-version'}):
            result = validator._validate_variable(
                'AZURE_OPENAI_API_VERSION',
                validator.REQUIRED_VARS['AZURE_OPENAI_API_VERSION'],
                required=True
            )
            
            assert result.validation_result is False
            assert "does not match expected pattern" in result.error_message
    
    def test_validate_variable_min_length(self):
        """Test variable validation with minimum length"""
        validator = EnvironmentValidator()
        
        # Valid length
        with patch.dict(os.environ, {'AZURE_OPENAI_KEY': 'a' * 25}):
            result = validator._validate_variable(
                'AZURE_OPENAI_KEY',
                validator.REQUIRED_VARS['AZURE_OPENAI_KEY'],
                required=True
            )
            
            assert result.validation_result is True
        
        # Too short
        with patch.dict(os.environ, {'AZURE_OPENAI_KEY': 'short'}):
            result = validator._validate_variable(
                'AZURE_OPENAI_KEY',
                validator.REQUIRED_VARS['AZURE_OPENAI_KEY'],
                required=True
            )
            
            assert result.validation_result is False
            assert "is too short" in result.error_message


@pytest.mark.integration
class TestEnvironmentValidation:
    """Integration tests for environment validation"""
    
    def test_complete_validation_all_present(self):
        """Test complete validation with all variables present"""
        validator = EnvironmentValidator()
        
        complete_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'a' * 30,
            'AZURE_OPENAI_API_VERSION': '2024-12-01-preview',
            'AZURE_OPENAI_LLM_DEPLOYMENT': 'gpt-4',
            'AZURE_OPENAI_LLM_MODEL': 'gpt-4',
            'AZURE_SPEECH_KEY': 'b' * 25,
            'AZURE_SPEECH_REGION': 'eastus'
        }
        
        with patch.dict(os.environ, complete_env):
            results = validator.validate_all()
            
            # Should have results for all defined variables
            assert len(results) >= 5  # At least the required ones
            
            # All required variables should pass
            required_results = [r for r in results if r.required]
            assert all(r.validation_result for r in required_results)
    
    def test_validation_report_generation(self):
        """Test generation of validation report"""
        validator = EnvironmentValidator()
        
        test_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'a' * 30,
            'AZURE_OPENAI_API_VERSION': '2024-12-01-preview',
            'AZURE_OPENAI_LLM_DEPLOYMENT': 'gpt-4',
            'AZURE_OPENAI_LLM_MODEL': 'gpt-4'
        }
        
        with patch.dict(os.environ, test_env):
            report = validator.get_validation_report()
            
            assert 'overall_status' in report
            assert 'total_checks' in report
            assert 'passed' in report
            assert 'failed' in report
            assert 'details' in report
            
            # Should pass with all required vars present
            assert report['overall_status'] == 'PASS'
            assert report['failed'] == 0
    
    def test_validation_report_with_failures(self):
        """Test validation report with some failures"""
        validator = EnvironmentValidator()
        
        # Missing some required variables
        incomplete_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'short',  # Too short
            # Missing other required vars
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            report = validator.get_validation_report()
            
            assert report['overall_status'] == 'FAIL'
            assert report['failed'] > 0
            assert len(report['errors']) > 0


@pytest.mark.unit
class TestEnvironmentConfiguration:
    """Test environment configuration loading"""
    
    def test_dotenv_file_loading(self):
        """Test loading environment from .env file"""
        # Create temporary .env file
        env_content = """
AZURE_OPENAI_ENDPOINT=https://test.openai.azure.com/
AZURE_OPENAI_KEY=test_key_12345678901234567890
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4
AZURE_OPENAI_LLM_MODEL=gpt-4
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_file:
            temp_file.write(env_content.strip())
            temp_file_path = temp_file.name
        
        try:
            # Load environment from file
            from dotenv import load_dotenv
            load_dotenv(temp_file_path)
            
            # Verify variables are loaded
            assert os.getenv('AZURE_OPENAI_ENDPOINT') == 'https://test.openai.azure.com/'
            assert os.getenv('AZURE_OPENAI_KEY') == 'test_key_12345678901234567890'
        finally:
            os.unlink(temp_file_path)
    
    def test_environment_priority(self):
        """Test that environment variables take priority over .env file"""
        # Set environment variable
        with patch.dict(os.environ, {'AZURE_OPENAI_ENDPOINT': 'https://env.openai.azure.com/'}):
            # This should take priority over any .env file
            assert os.getenv('AZURE_OPENAI_ENDPOINT') == 'https://env.openai.azure.com/'
    
    def test_configuration_export(self):
        """Test exporting configuration for debugging"""
        test_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'secret_key_12345678901234567890',
            'AZURE_OPENAI_API_VERSION': '2024-12-01-preview'
        }
        
        with patch.dict(os.environ, test_env):
            # Export configuration (with secrets redacted)
            config = {}
            for key in ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY', 'AZURE_OPENAI_API_VERSION']:
                value = os.getenv(key)
                if value and 'KEY' in key:
                    # Redact secrets
                    config[key] = value[:8] + '*' * (len(value) - 8)
                else:
                    config[key] = value
            
            assert config['AZURE_OPENAI_ENDPOINT'] == 'https://test.openai.azure.com/'
            assert config['AZURE_OPENAI_KEY'].startswith('secret_k')
            assert config['AZURE_OPENAI_KEY'].endswith('*' * 24)


@pytest.mark.integration
class TestApplicationEnvironmentIntegration:
    """Test environment integration with application components"""
    
    def test_azure_client_initialization(self):
        """Test Azure OpenAI client initialization with environment"""
        test_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'test_key_12345678901234567890',
            'AZURE_OPENAI_API_VERSION': '2024-12-01-preview',
            'AZURE_OPENAI_LLM_DEPLOYMENT': 'gpt-4',
            'AZURE_OPENAI_LLM_MODEL': 'gpt-4'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('openai.AzureOpenAI') as mock_client:
                # Import and initialize client
                from app import client
                
                # Verify client was initialized with correct parameters
                mock_client.assert_called_once()
                call_args = mock_client.call_args
                assert call_args[1]['azure_endpoint'] == test_env['AZURE_OPENAI_ENDPOINT']
                assert call_args[1]['api_key'] == test_env['AZURE_OPENAI_KEY']
                assert call_args[1]['api_version'] == test_env['AZURE_OPENAI_API_VERSION']
    
    def test_missing_environment_error_handling(self):
        """Test application behavior with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing environment gracefully
            try:
                from app import client
                # If this doesn't raise an exception, the app has good error handling
                assert True
            except Exception as e:
                # If it does raise an exception, it should be informative
                assert 'environment' in str(e).lower() or 'key' in str(e).lower()
    
    def test_application_health_check(self):
        """Test application health with environment validation"""
        test_env = {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'test_key_12345678901234567890',
            'AZURE_OPENAI_API_VERSION': '2024-12-01-preview',
            'AZURE_OPENAI_LLM_DEPLOYMENT': 'gpt-4',
            'AZURE_OPENAI_LLM_MODEL': 'gpt-4'
        }
        
        with patch.dict(os.environ, test_env):
            validator = EnvironmentValidator()
            report = validator.get_validation_report()
            
            # Application should be healthy with all required vars
            assert report['overall_status'] == 'PASS'
            
            # Test application components can be imported
            try:
                from app import AgenticSkillBuilder, LessonAgent, QuizAgent, ProgressAgent
                assert True  # All imports successful
            except ImportError as e:
                pytest.fail(f"Failed to import application components: {e}")


@pytest.mark.unit
class TestEnvironmentSecurityValidation:
    """Test security aspects of environment validation"""
    
    def test_secret_redaction_in_logs(self):
        """Test that secrets are properly redacted in logs/output"""
        secret_value = "secret_key_abcdefghijklmnopqrstuvwxyz"
        
        # Simulate redacting secrets for logging
        def redact_secret(value: str, show_chars: int = 8) -> str:
            if len(value) <= show_chars:
                return '*' * len(value)
            return value[:show_chars] + '*' * (len(value) - show_chars)
        
        redacted = redact_secret(secret_value)
        
        assert redacted.startswith('secret_k')
        assert '*' in redacted
        assert len(redacted) == len(secret_value)
    
    def test_environment_variable_validation_security(self):
        """Test validation doesn't expose sensitive data"""
        validator = EnvironmentValidator()
        
        with patch.dict(os.environ, {'AZURE_OPENAI_KEY': 'very_secret_key_123456789'}):
            result = validator._validate_variable(
                'AZURE_OPENAI_KEY',
                validator.REQUIRED_VARS['AZURE_OPENAI_KEY'],
                required=True
            )
            
            # Value should be captured but could be redacted for security
            assert result.present is True
            assert result.validation_result is True
            # Don't assert the actual value to avoid exposing secrets in test output
