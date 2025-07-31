# Adicionar estes endpoints ao main_simple.py

# ========================================
# MAINTENANCE AND CLEANUP ENDPOINTS
# ========================================

from pathlib import Path
import shutil
import hashlib
from collections import defaultdict
from typing import List, Dict, Any

@app.post("/maintenance/cleanup-duplicates")
async def cleanup_duplicate_files(current_user: User = Depends(get_current_user)):
    """Remove duplicate files from materials directory based on content hash"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"🧹 Cleanup duplicates requested by: {current_user.username}")
    
    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"status": "success", "message": "No materials directory found", "removed_files": 0}
        
        # Calculate hashes for all files
        file_hashes = defaultdict(list)
        total_files = 0
        
        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    file_hashes[file_hash].append(file_path)
                except Exception as e:
                    logger.warning(f"Could not hash file {file_path}: {e}")
        
        # Find and remove duplicates
        removed_files = 0
        duplicate_groups = 0
        saved_space = 0
        
        for file_hash, file_paths in file_hashes.items():
            if len(file_paths) > 1:
                duplicate_groups += 1
                # Keep the first file, remove the rest
                for duplicate_file in file_paths[1:]:
                    try:
                        file_size = duplicate_file.stat().st_size
                        duplicate_file.unlink()
                        removed_files += 1
                        saved_space += file_size
                        logger.info(f"🗑️ Removed duplicate: {duplicate_file}")
                    except Exception as e:
                        logger.error(f"Error removing duplicate {duplicate_file}: {e}")
        
        return {
            "status": "success",
            "message": f"Cleanup completed",
            "statistics": {
                "total_files_scanned": total_files,
                "duplicate_groups_found": duplicate_groups,
                "files_removed": removed_files,
                "space_saved_bytes": saved_space,
                "space_saved_mb": round(saved_space / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")

@app.post("/maintenance/cleanup-empty-folders")
async def cleanup_empty_folders(current_user: User = Depends(get_current_user)):
    """Remove empty folders from materials directory"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"📁 Empty folder cleanup requested by: {current_user.username}")
    
    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"status": "success", "message": "No materials directory found", "removed_folders": 0}
        
        removed_folders = 0
        
        # Remove empty folders (bottom-up approach)
        for folder_path in sorted(materials_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if folder_path.is_dir() and folder_path != materials_dir:
                try:
                    if not any(folder_path.iterdir()):  # Check if folder is empty
                        folder_path.rmdir()
                        removed_folders += 1
                        logger.info(f"🗑️ Removed empty folder: {folder_path}")
                except Exception as e:
                    logger.warning(f"Could not remove folder {folder_path}: {e}")
        
        return {
            "status": "success",
            "message": f"Empty folder cleanup completed",
            "removed_folders": removed_folders
        }
        
    except Exception as e:
        logger.error(f"❌ Error during folder cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Folder cleanup error: {str(e)}")

@app.post("/maintenance/reset-materials")
async def reset_materials_directory(current_user: User = Depends(get_current_user)):
    """Completely reset the materials directory"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"🔄 Materials reset requested by: {current_user.username}")
    
    try:
        materials_dir = Path("data/materials")
        
        if materials_dir.exists():
            # Count files before deletion
            file_count = len([f for f in materials_dir.rglob("*") if f.is_file()])
            folder_count = len([f for f in materials_dir.rglob("*") if f.is_dir()])
            
            # Remove entire directory
            shutil.rmtree(materials_dir)
            logger.info(f"🗑️ Removed materials directory with {file_count} files and {folder_count} folders")
        else:
            file_count = 0
            folder_count = 0
        
        # Recreate empty directory
        materials_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📁 Created new empty materials directory")
        
        return {
            "status": "success",
            "message": "Materials directory reset completed",
            "removed_files": file_count,
            "removed_folders": folder_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error during materials reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Materials reset error: {str(e)}")

@app.post("/maintenance/reset-chromadb")
async def reset_chromadb(current_user: User = Depends(get_current_user)):
    """Reset ChromaDB vector database"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"🗄️ ChromaDB reset requested by: {current_user.username}")
    
    try:
        global rag_handler
        
        # Reset RAG handler
        if rag_handler:
            rag_handler.reset()
            logger.info("🔄 RAG handler reset")
        
        # Remove ChromaDB directory
        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            shutil.rmtree(chromadb_dir)
            logger.info("🗑️ Removed ChromaDB directory")
        
        # Reset global RAG handler
        rag_handler = None
        
        return {
            "status": "success",
            "message": "ChromaDB reset completed",
            "note": "You will need to reinitialize the system to use chat functionality"
        }
        
    except Exception as e:
        logger.error(f"❌ Error during ChromaDB reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ChromaDB reset error: {str(e)}")

@app.get("/maintenance/system-report")
async def generate_system_report(current_user: User = Depends(get_current_user)):
    """Generate comprehensive system report"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    logger.info(f"📊 System report requested by: {current_user.username}")
    
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "generated_by": current_user.username,
            "system_info": {
                "version": "1.4.0",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": os.name
            },
            "directories": {},
            "drive_status": {},
            "rag_status": {},
            "file_analysis": {},
            "recommendations": []
        }
        
        # Directory analysis
        materials_dir = Path("data/materials")
        chromadb_dir = Path(".chromadb")
        
        if materials_dir.exists():
            all_files = list(materials_dir.rglob("*"))
            files = [f for f in all_files if f.is_file()]
            folders = [f for f in all_files if f.is_dir()]
            
            total_size = sum(f.stat().st_size for f in files)
            
            # File type analysis
            file_types = defaultdict(int)
            for file in files:
                ext = file.suffix.lower() or 'no_extension'
                file_types[ext] += 1
            
            # Size distribution
            size_ranges = {
                "< 1MB": 0,
                "1MB - 10MB": 0,
                "10MB - 100MB": 0,
                "> 100MB": 0
            }
            
            for file in files:
                size = file.stat().st_size
                if size < 1024 * 1024:
                    size_ranges["< 1MB"] += 1
                elif size < 10 * 1024 * 1024:
                    size_ranges["1MB - 10MB"] += 1
                elif size < 100 * 1024 * 1024:
                    size_ranges["10MB - 100MB"] += 1
                else:
                    size_ranges["> 100MB"] += 1
            
            report["directories"]["materials"] = {
                "exists": True,
                "total_files": len(files),
                "total_folders": len(folders),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": dict(file_types),
                "size_distribution": size_ranges
            }
        else:
            report["directories"]["materials"] = {"exists": False}
        
        report["directories"]["chromadb"] = {
            "exists": chromadb_dir.exists(),
            "size_bytes": sum(f.stat().st_size for f in chromadb_dir.rglob("*") if f.is_file()) if chromadb_dir.exists() else 0
        }
        
        # Drive status
        report["drive_status"] = {
            "handler_initialized": drive_handler is not None,
            "service_available": drive_handler.service is not None if drive_handler else False,
            "authentication_method": "API Key" if (drive_handler and drive_handler.api_key) else "OAuth2" if (drive_handler and drive_handler.service) else "None",
            "processed_files_count": len(drive_handler.processed_files) if drive_handler else 0,
            "unique_hashes_count": len(drive_handler.file_hashes) if drive_handler else 0
        }
        
        # RAG status
        report["rag_status"] = {
            "initialized": rag_handler is not None,
            "stats": rag_handler.get_system_stats() if rag_handler else {}
        }
        
        # Duplicate analysis
        if materials_dir.exists():
            duplicate_analysis = analyze_duplicates(materials_dir)
            report["file_analysis"]["duplicates"] = duplicate_analysis
        
        # Generate recommendations
        recommendations = []
        
        if not report["drive_status"]["service_available"]:
            recommendations.append("Configure Google Drive authentication for sync functionality")
        
        if not report["rag_status"]["initialized"]:
            recommendations.append("Initialize RAG system for chat functionality")
        
        if report["directories"]["materials"]["exists"]:
            if report["file_analysis"].get("duplicates", {}).get("duplicate_groups", 0) > 0:
                recommendations.append("Run duplicate cleanup to save storage space")
            
            if report["directories"]["materials"]["total_files"] == 0:
                recommendations.append("Sync materials from Google Drive or upload files manually")
        
        report["recommendations"] = recommendations
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Error generating system report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

def analyze_duplicates(materials_dir: Path) -> Dict[str, Any]:
    """Analyze duplicate files in materials directory"""
    try:
        file_hashes = defaultdict(list)
        total_files = 0
        
        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    file_hashes[file_hash].append({
                        "path": str(file_path.relative_to(materials_dir)),
                        "size": file_path.stat().st_size
                    })
                except Exception:
                    continue
        
        duplicate_groups = 0
        duplicate_files = 0
        wasted_space = 0
        
        for file_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                duplicate_groups += 1
                duplicate_files += len(file_list) - 1
                # Calculate wasted space (all duplicates except the first)
                file_size = file_list[0]["size"]
                wasted_space += file_size * (len(file_list) - 1)
        
        return {
            "total_files_scanned": total_files,
            "unique_files": len(file_hashes),
            "duplicate_groups": duplicate_groups,
            "duplicate_files": duplicate_files,
            "wasted_space_bytes": wasted_space,
            "wasted_space_mb": round(wasted_space / (1024 * 1024), 2),
            "efficiency_percentage": round((1 - duplicate_files / total_files) * 100, 2) if total_files > 0 else 100
        }
        
    except Exception as e:
        logger.error(f"Error analyzing duplicates: {e}")
        return {"error": str(e)}

@app.post("/maintenance/optimize-storage")
async def optimize_storage(current_user: User = Depends(get_current_user)):
    """Run comprehensive storage optimization"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"⚡ Storage optimization requested by: {current_user.username}")
    
    try:
        results = {
            "duplicate_cleanup": None,
            "empty_folder_cleanup": None,
            "total_space_saved": 0,
            "optimization_time": 0
        }
        
        start_time = time.time()
        
        # Run duplicate cleanup
        try:
            duplicate_response = await cleanup_duplicate_files(current_user)
            results["duplicate_cleanup"] = duplicate_response
            if "statistics" in duplicate_response:
                results["total_space_saved"] += duplicate_response["statistics"]["space_saved_bytes"]
        except Exception as e:
            results["duplicate_cleanup"] = {"error": str(e)}
        
        # Run empty folder cleanup
        try:
            folder_response = await cleanup_empty_folders(current_user)
            results["empty_folder_cleanup"] = folder_response
        except Exception as e:
            results["empty_folder_cleanup"] = {"error": str(e)}
        
        results["optimization_time"] = round(time.time() - start_time, 2)
        results["total_space_saved_mb"] = round(results["total_space_saved"] / (1024 * 1024), 2)
        
        return {
            "status": "success",
            "message": "Storage optimization completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error during storage optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage optimization error: {str(e)}")

# Import necessary modules at the top of main_simple.py
import sys
import time
