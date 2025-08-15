#!/usr/bin/env ./venv/bin/python3
"""
Test Essentia installation and basic functionality
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_essentia_import():
    """Test Essentia import and basic functionality"""
    try:
        import essentia
        import essentia.standard as es
        
        logger.info(f"✅ Essentia imported successfully")
        logger.info(f"   Version: {essentia.__version__}")
        
        # Test basic algorithm creation
        windowing = es.Windowing(type='hann')
        spectrum = es.Spectrum()
        mfcc = es.MFCC()
        
        logger.info("✅ Basic algorithms created successfully")
        
        # List some available algorithms
        logger.info("Available audio analysis algorithms:")
        algorithms = [
            "Tempo", "Key", "Loudness", "SpectralCentroid", 
            "ZeroCrossingRate", "RollOff", "MFCC", "ChromaShift"
        ]
        
        for algo_name in algorithms:
            try:
                algo = getattr(es, algo_name)
                logger.info(f"   ✅ {algo_name}")
            except AttributeError:
                logger.info(f"   ❌ {algo_name} not available")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import Essentia: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Essentia: {e}")
        return False

def test_audio_analysis_pipeline():
    """Test a complete audio analysis pipeline"""
    try:
        import essentia.standard as es
        import numpy as np
        
        logger.info("🎵 Testing audio analysis pipeline...")
        
        # Create a synthetic audio signal for testing
        sample_rate = 44100
        duration = 1.0  # 1 second
        frequency = 440.0  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        logger.info(f"   Generated test audio: {len(audio)} samples at {sample_rate}Hz")
        
        # Analyze with Essentia
        algorithms = {
            'key': es.KeyExtractor(),
            'loudness': es.Loudness(),
            'zcr': es.ZeroCrossingRate(),
            'rolloff': es.RollOff(),
        }
        
        results = {}
        
        for name, algorithm in algorithms.items():
            try:
                if name == 'key':
                    result = algorithm(audio)
                    results[name] = {'key': result[0], 'scale': result[1], 'strength': result[2]}
                    logger.info(f"   ✅ Key: {result[0]} {result[1]} (strength: {result[2]:.2f})")
                    continue
                elif name == 'loudness':
                    result = algorithm(audio)
                elif name in ['zcr', 'rolloff']:
                    # These need frame-by-frame analysis
                    windowing = es.Windowing(type='hann')
                    spectrum = es.Spectrum()
                    
                    frame_size = 2048
                    hop_size = 1024
                    
                    values = []
                    for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
                        windowed = windowing(frame)
                        
                        if name == 'zcr':
                            values.append(algorithm(frame))
                        else:  # rolloff
                            spec = spectrum(windowed)
                            values.append(algorithm(spec))
                    
                    result = np.mean(values) if values else 0.0
                
                results[name] = result
                logger.info(f"   ✅ {name.title()}: {result}")
                
            except Exception as e:
                logger.warning(f"   ❌ {name} failed: {e}")
        
        logger.info("✅ Audio analysis pipeline test completed")
        return results
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        return None

def main():
    """Test Essentia installation and functionality"""
    
    print("🎵 Essentia Installation Test")
    print("=" * 40)
    
    # Test 1: Import
    if not test_essentia_import():
        print("❌ Essentia installation failed")
        return
    
    # Test 2: Audio analysis pipeline
    results = test_audio_analysis_pipeline()
    if results:
        print("\n✅ Essentia is ready for audio analysis!")
        print("Available for integration into enhanced audio features system")
    else:
        print("❌ Audio analysis pipeline failed")

if __name__ == "__main__":
    main()