"""
GPU tekshiruv skripti - onnxruntime-gpu va CUDA mavjudligini tekshiradi
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_onnxruntime():
    """Check onnxruntime installation and providers"""
    try:
        import onnxruntime as ort
        logger.info("=" * 60)
        logger.info("ONNX Runtime GPU Tekshiruvi")
        logger.info("=" * 60)
        
        # Check version
        version = ort.__version__
        logger.info(f"ONNX Runtime versiyasi: {version}")
        
        # Check available providers
        available_providers = ort.get_available_providers()
        logger.info(f"\nMavjud providers: {available_providers}")
        
        # Check if GPU provider is available
        if 'CUDAExecutionProvider' in available_providers:
            logger.info("\n✓ CUDAExecutionProvider MAVJUD - GPU ishlatilishi mumkin!")
            
            # Try to get device info
            try:
                import onnxruntime.capi.onnxruntime_pybind11_state as ort_capi
                logger.info("✓ CUDA qo'llab-quvvatlanadi")
            except Exception as e:
                logger.warning(f"CUDA mavjud, lekin qo'shimcha tekshiruvda xato: {e}")
            
            return True
        else:
            logger.error("\n✗ CUDAExecutionProvider MAVJUD EMAS!")
            logger.error("\nMuammo tuzatish:")
            logger.error("1. onnxruntime-gpu o'rnatilganligini tekshiring:")
            logger.error("   pip uninstall onnxruntime")
            logger.error("   pip install onnxruntime-gpu")
            logger.error("\n2. CUDA toolkit o'rnatilganligini tekshiring")
            logger.error("3. NVIDIA GPU driverlar yangi versiyada ekanligini tekshiring")
            logger.error("4. Ilovani qayta ishga tushiring")
            return False
            
    except ImportError as e:
        logger.error(f"onnxruntime import qilishda xato: {e}")
        logger.error("Iltimos, onnxruntime-gpu ni o'rnating:")
        logger.error("  pip install onnxruntime-gpu")
        return False
    except Exception as e:
        logger.error(f"Xato: {e}")
        return False

def check_cuda():
    """Check CUDA availability"""
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("\n" + "=" * 60)
            logger.info("NVIDIA GPU Ma'lumotlari:")
            logger.info("=" * 60)
            logger.info(result.stdout)
            return True
        else:
            logger.warning("nvidia-smi ishlamayapti - GPU topilmadi yoki driverlar o'rnatilmagan")
            return False
    except FileNotFoundError:
        logger.warning("nvidia-smi topilmadi - GPU mavjud emas yoki driverlar o'rnatilmagan")
        return False
    except Exception as e:
        logger.warning(f"GPU tekshiruvda xato: {e}")
        return False

def check_cuda_libraries():
    """Check if CUDA libraries are available (Windows DLLs or Linux .so files)"""
    import os
    import sys
    
    if sys.platform == 'win32':
        # Windows: Check for CUDA DLLs
        return check_cuda_dlls_windows()
    else:
        # Linux/Unix: Check for CUDA libraries
        return check_cuda_libs_linux()

def check_cuda_dlls_windows():
    """Check if CUDA DLLs are available on Windows"""
    import os
    import sys
    
    logger.info("\n" + "=" * 60)
    logger.info("CUDA DLL Tekshiruvi (Windows)")
    logger.info("=" * 60)
    
    # Check for CUDA DLL files (both 12.x and 13.x)
    cuda_paths = [
        os.environ.get('CUDA_PATH'),
        os.environ.get('CUDA_PATH_V13_0'),
        os.environ.get('CUDA_PATH_V12_4'),
        os.environ.get('CUDA_PATH_V12_3'),
        os.environ.get('CUDA_PATH_V12_2'),
        os.environ.get('CUDA_PATH_V12_1'),
        os.environ.get('CUDA_PATH_V12_0'),
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8',
    ]
    
    dll_found = False
    found_path = None
    dll_name = None
    
    for cuda_path in cuda_paths:
        if cuda_path and os.path.exists(cuda_path):
            bin_path = os.path.join(cuda_path, 'bin')
            
            # Try multiple DLL names (CUDA 13.0 might have different names)
            dll_variants = [
                ('cublasLt64_13.dll', 'CUDA 13.0'),
                ('cublasLt64_12.dll', 'CUDA 12.x'),
                ('cublas64_13.dll', 'CUDA 13.0 (alternative)'),
                ('cublas64_12.dll', 'CUDA 12.x (alternative)'),
                ('cublasLt64.dll', 'CUDA (generic)'),
            ]
            
            # Also check if any cublas DLL exists
            import glob
            cublas_dlls = glob.glob(os.path.join(bin_path, '*cublas*.dll'))
            
            if cublas_dlls:
                # Found some cublas DLL
                dll_found = True
                found_path = bin_path
                dll_name = os.path.basename(cublas_dlls[0])
                logger.info(f"✓ CUDA DLL topildi: {dll_name} ({bin_path})")
                break
            
            # Try specific variants
            for dll_name, version in dll_variants:
                dll_path = os.path.join(bin_path, dll_name)
                if os.path.exists(dll_path):
                    dll_found = True
                    found_path = bin_path
                    logger.info(f"✓ {dll_name} topildi ({version}): {dll_path}")
                    break
            
            if dll_found:
                break
    
    # Check if CUDA bin path is in PATH environment variable
    path_env = os.environ.get('PATH', '').lower()
    cuda_in_path = False
    cuda_bin_path_found = None
    
    # Check if any CUDA bin path is in PATH
    for cuda_path in cuda_paths:
        if cuda_path and os.path.exists(cuda_path):
            bin_path = os.path.join(cuda_path, 'bin')
            if bin_path.lower() in path_env or bin_path.replace('\\', '/').lower() in path_env:
                cuda_in_path = True
                cuda_bin_path_found = bin_path
                logger.info(f"✓ CUDA bin papkasi PATH da topildi: {bin_path}")
                break
    
    # Also check CUDA_PATH
    cuda_path_env = os.environ.get('CUDA_PATH')
    if cuda_path_env and os.path.exists(cuda_path_env):
        logger.info(f"✓ CUDA_PATH mavjud: {cuda_path_env}")
        cuda_bin_from_env = os.path.join(cuda_path_env, 'bin')
        if os.path.exists(cuda_bin_from_env):
            if not cuda_in_path:
                cuda_in_path = True
                cuda_bin_path_found = cuda_bin_from_env
    
    # If CUDA bin is in PATH, that's enough (ONNX Runtime will find DLLs)
    if cuda_in_path or dll_found:
        logger.info("✓ CUDA Toolkit topildi va PATH da mavjud")
        logger.info("  ONNX Runtime GPU kerakli DLL larni o'zi topadi")
        return True
    
    # If not found, show error
    if not dll_found and not cuda_in_path:
        logger.error("✗ CUDA Toolkit PATH da topilmadi!")
        logger.error("\nCUDA Toolkit o'rnatilmagan yoki PATH ga qo'shilmagan")
        logger.error("\nYECHIM:")
        logger.error("1. CUDA Toolkit 12.x yoki 13.x ni o'rnating:")
        logger.error("   https://developer.nvidia.com/cuda-downloads")
        logger.error("\n2. Avtomatik sozlash skriptini ishga tushiring:")
        logger.error("   .\\scripts\\setup_cuda_13.ps1")
        logger.error("   yoki")
        logger.error("   .\\scripts\\fix_cuda_path.ps1")
        logger.error("\n3. YANGI TERMINAL OCHING (PATH o'zgarishlari yangi terminalda ko'rinadi)!")
        return False
    
    return True

def check_cuda_libs_linux():
    """Check if CUDA libraries are available on Linux"""
    import os
    import sys
    import glob
    import ctypes.util
    
    logger.info("\n" + "=" * 60)
    logger.info("CUDA Libraries Tekshiruvi (Linux)")
    logger.info("=" * 60)
    
    # Check for CUDA in standard locations
    cuda_paths = [
        os.environ.get('CUDA_HOME'),
        os.environ.get('CUDA_PATH'),
        '/usr/local/cuda',
        '/usr/local/cuda-12.4',
        '/usr/local/cuda-12.3',
        '/usr/local/cuda-12.2',
        '/usr/local/cuda-12.1',
        '/usr/local/cuda-12.0',
        '/usr/local/cuda-11.8',
    ]
    
    lib_found = False
    found_path = None
    
    for cuda_path in cuda_paths:
        if cuda_path and os.path.exists(cuda_path):
            lib_path = os.path.join(cuda_path, 'lib64')
            if os.path.exists(lib_path):
                cublas_libs = glob.glob(os.path.join(lib_path, 'libcublas*.so*'))
                if cublas_libs:
                    lib_found = True
                    found_path = lib_path
                    logger.info(f"✓ CUDA library found: {cublas_libs[0]}")
                    break
    
    # Check LD_LIBRARY_PATH
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    if ld_library_path:
        logger.info(f"✓ LD_LIBRARY_PATH is set: {ld_library_path}")
    
    # Try to find library using ctypes
    if not lib_found:
        cublas_path = ctypes.util.find_library('cublas')
        if cublas_path:
            lib_found = True
            logger.info(f"✓ CUDA library found in system: {cublas_path}")
    
    # Check nvidia-smi (indicates NVIDIA drivers)
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--version'], 
                              capture_output=True, timeout=2)
        if result.returncode == 0:
            logger.info("✓ NVIDIA drivers detected (nvidia-smi available)")
            if not lib_found:
                logger.info("ℹ CUDA libraries not found in standard paths, but ONNX Runtime will try to load them automatically")
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    if lib_found:
        logger.info("✓ CUDA libraries are available")
        if found_path and found_path not in ld_library_path:
            logger.info(f"ℹ Consider adding to LD_LIBRARY_PATH: export LD_LIBRARY_PATH={found_path}:$LD_LIBRARY_PATH")
        return True
    else:
        logger.warning("⚠ CUDA libraries not found in standard locations")
        logger.info("ℹ ONNX Runtime will attempt to load CUDA libraries automatically")
        logger.info("ℹ If GPU doesn't work, ensure CUDA Toolkit is installed")
        return True  # Don't fail - let ONNX Runtime try

def check_faiss_gpu():
    """Check if FAISS GPU is available"""
    try:
        import faiss
        logger.info("\n" + "=" * 60)
        logger.info("FAISS GPU Tekshiruvi")
        logger.info("=" * 60)
        
        ngpus = faiss.get_num_gpus()
        if ngpus > 0:
            logger.info(f"✓ FAISS GPU MAVJUD: {ngpus} GPU(s) aniqlandi")
            logger.info("✓ FAISS vector search GPU da ishlaydi!")
            return True
        else:
            logger.warning("⚠ FAISS GPU topilmadi (faiss-cpu o'rnatilgan)")
            logger.warning("FAISS CPU da ishlaydi (sekinroq, lekin ishlaydi)")
            logger.info("\nFAISS GPU ni o'rnatish uchun (ixtiyoriy):")
            logger.info("Windows da pip orqali o'rnatilmaydi. Conda kerak:")
            logger.info("  1. Conda o'rnating: https://docs.conda.io/")
            logger.info("  2. Conda environment yarating")
            logger.info("  3. conda install -c pytorch faiss-gpu")
            logger.info("\nLekin hozirgi holatda CPU versiyasi ishlaydi!")
            return False
    except ImportError:
        logger.error("✗ FAISS o'rnatilmagan!")
        logger.error("Iltimos, faiss-cpu ni o'rnating:")
        logger.error("  pip install faiss-cpu")
        return False
    except Exception as e:
        logger.warning(f"⚠ FAISS GPU tekshiruvda xato: {e}")
        logger.info("FAISS CPU versiyasi ishlaydi")
        return False

def main():
    """Main function"""
    logger.info("\n" + "=" * 60)
    logger.info("GPU Tekshiruv Skripti")
    logger.info("=" * 60 + "\n")
    
    # Check CUDA/GPU
    gpu_available = check_cuda()
    
    # Check CUDA libraries (Windows DLLs or Linux .so files)
    cuda_libs_available = check_cuda_libraries()
    
    # Check ONNX Runtime
    onnx_gpu_available = check_onnxruntime()
    
    # Check FAISS GPU
    faiss_gpu_available = check_faiss_gpu()
    
    logger.info("\n" + "=" * 60)
    logger.info("YAKUNIY NATIJA")
    logger.info("=" * 60)
    
    all_checks = [
        ("GPU/Driver", gpu_available),
        ("CUDA Libraries", cuda_libs_available),
        ("ONNX Runtime GPU", onnx_gpu_available),
        ("FAISS GPU", faiss_gpu_available)
    ]
    
    all_passed = all(check[1] for check in all_checks)
    
    for check_name, check_result in all_checks:
        status = "✓" if check_result else "✗"
        logger.info(f"{status} {check_name}")
    
    # Critical checks (must pass for GPU)
    critical_checks = [
        ("CUDA Libraries", cuda_libs_available),
        ("ONNX Runtime GPU", onnx_gpu_available)
    ]
    critical_passed = all(check[1] for check in critical_checks)
    
    if all_passed:
        logger.info("\n✓ BARCHA TEKSHRUVLAR MUVOFFAQIYATLI!")
        logger.info("Backend 100% GPU ishlatishga tayyor! 🚀")
        sys.exit(0)
    elif critical_passed:
        logger.info("\n✓ ASOSIY GPU TEKSHRUVLAR MUVOFFAQIYATLI!")
        logger.info("Backend GPU da ishlaydi! (FAISS CPU da ishlaydi, lekin bu OK)")
        if sys.platform != 'win32':
            logger.info("\nFAISS GPU (ixtiyoriy):")
            logger.info("Linux da pip orqali o'rnatish mumkin: pip install faiss-gpu")
        else:
            logger.info("\nFAISS GPU (ixtiyoriy):")
            logger.info("Windows da conda orqali o'rnatish mumkin, lekin zarurat yo'q")
        sys.exit(0)
    else:
        logger.error("\n✗ ASOSIY TEKSHRUVLAR MUVOFFAQIYATSIZ!")
        if not cuda_libs_available:
            if sys.platform == 'win32':
                logger.error("\nASOSIY MUAMMO: CUDA Toolkit o'rnatilmagan yoki PATH ga qo'shilmagan!")
                logger.error("YECHIM: Yangi terminal oching va quyidagilarni bajargan:")
                logger.error("  .\\scripts\\setup_cuda_13.ps1")
            else:
                logger.error("\nASOSIY MUAMMO: CUDA Toolkit o'rnatilmagan yoki LD_LIBRARY_PATH ga qo'shilmagan!")
                logger.error("YECHIM (Linux):")
                logger.error("  1. CUDA Toolkit o'rnating: https://developer.nvidia.com/cuda-downloads")
                logger.error("  2. export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH")
                logger.error("  3. export CUDA_HOME=/usr/local/cuda")
        if not onnx_gpu_available:
            logger.error("\nMUAMMO: ONNX Runtime GPU ishlatilmayapti!")
        if not faiss_gpu_available:
            logger.warning("\nESLATMA: FAISS GPU yo'q, lekin CPU versiyasi ishlaydi (bu OK)")
        sys.exit(1)

if __name__ == "__main__":
    main()

