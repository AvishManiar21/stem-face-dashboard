"""Application entry point"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("STEM Tutor Scheduling System")
    print("=" * 60)
    print(f"Face Recognition: {'ENABLED' if app.config['ENABLE_FACE_RECOGNITION'] else 'DISABLED'}")
    print(f"Legacy Analytics: {'ENABLED' if app.config['ENABLE_LEGACY_ANALYTICS'] else 'DISABLED'}")
    print(f"Maintenance Mode: {'ENABLED' if app.config['MAINTENANCE_MODE'] else 'DISABLED'}")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
