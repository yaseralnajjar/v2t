"""Unit tests for transcriber.py - AudioTranscriber class."""

from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest


class TestAudioTranscriberInit:
    """Tests for AudioTranscriber initialization."""

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_init_loads_model_from_config(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that __init__ uses model name from config."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        assert transcriber.model_name == "tiny.en"

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_init_uses_local_model_if_exists(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that __init__ uses local model file if it exists."""
        mock_config.MODEL = "small.en"
        mock_isfile.return_value = False
        mock_exists.return_value = True

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        call_args = mock_model.call_args
        assert "ggml-model.bin" in call_args[0][0]

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_init_uses_full_path_if_provided(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that __init__ uses full path if MODEL is a file path."""
        mock_config.MODEL = "/path/to/custom/model.bin"
        mock_isfile.return_value = True

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        mock_model.assert_called_once()
        assert mock_model.call_args[0][0] == "/path/to/custom/model.bin"


class TestAudioTranscriberGetModelName:
    """Tests for AudioTranscriber.get_model_name() method."""

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_get_model_name_returns_configured_model(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that get_model_name returns the configured model name."""
        mock_config.MODEL = "medium.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()
        result = transcriber.get_model_name()

        assert result == "medium.en"


class TestAudioTranscriberTranscribe:
    """Tests for AudioTranscriber.transcribe() method."""

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_returns_empty_string_for_empty_audio(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe returns empty string for empty audio."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(np.array([]))

        assert result == ""

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_flattens_multichannel_audio(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe flattens multi-dimensional audio."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        mock_segment = MagicMock()
        mock_segment.text = "hello"
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [mock_segment]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        audio_2d = np.array([[0.1], [0.2], [0.3]])
        transcriber.transcribe(audio_2d)

        call_args = mock_model_instance.transcribe.call_args[0][0]
        assert call_args.ndim == 1

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_converts_to_float32(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe converts audio to float32."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [mock_segment]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        audio_int16 = np.array([100, 200, 300], dtype=np.int16)
        transcriber.transcribe(audio_int16)

        call_args = mock_model_instance.transcribe.call_args[0][0]
        assert call_args.dtype == np.float32

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_normalizes_quiet_audio(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe normalizes quiet audio."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        mock_segment = MagicMock()
        mock_segment.text = "quiet"
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [mock_segment]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        quiet_audio = np.array([0.01, 0.02, 0.03], dtype=np.float32)
        transcriber.transcribe(quiet_audio)

        call_args = mock_model_instance.transcribe.call_args[0][0]
        assert np.max(np.abs(call_args)) > np.max(np.abs(quiet_audio))

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_concatenates_segments(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe concatenates multiple segments."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        segment1 = MagicMock()
        segment1.text = "Hello "
        segment2 = MagicMock()
        segment2.text = "world"
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [segment1, segment2]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32))

        assert result == "Hello world"

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_strips_whitespace(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe strips leading/trailing whitespace."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        segment = MagicMock()
        segment.text = "  hello world  "
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [segment]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32))

        assert result == "hello world"

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_handles_exception(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe handles exceptions gracefully."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.side_effect = Exception("Model error")
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32))

        assert result == ""

    @patch('transcriber.config')
    @patch('transcriber.Model')
    @patch('transcriber.os.path.isfile')
    @patch('transcriber.os.path.exists')
    def test_transcribe_does_not_normalize_loud_audio(self, mock_exists, mock_isfile, mock_model, mock_config):
        """Test that transcribe doesn't normalize audio that's already loud enough."""
        mock_config.MODEL = "tiny.en"
        mock_isfile.return_value = False
        mock_exists.return_value = False

        mock_segment = MagicMock()
        mock_segment.text = "loud"
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = [mock_segment]
        mock_model.return_value = mock_model_instance

        from transcriber import AudioTranscriber

        transcriber = AudioTranscriber()

        loud_audio = np.array([0.6, 0.7, 0.8], dtype=np.float32)
        transcriber.transcribe(loud_audio)

        call_args = mock_model_instance.transcribe.call_args[0][0]
        np.testing.assert_array_almost_equal(call_args, loud_audio)
