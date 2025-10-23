#!/usr/bin/env python3
"""
Script to fix demo video paths in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Template

def fix_demo_paths():
    """Fix demo video paths in the database"""
    templates = Template.objects.filter(demo_video__isnull=False)
    
    print(f"Found {templates.count()} templates with demo videos")
    
    for template in templates:
        old_path = template.demo_video.path
        print(f"Template {template.id}: {old_path}")
        
        # Check if the file exists in the old location
        if os.path.exists(old_path):
            # The file exists, we just need to update the database path
            # The actual file path should be correct now with the model change
            print(f"  File exists: {old_path}")
        else:
            # Try to find the file in the correct location
            filename = os.path.basename(old_path)
            correct_path = os.path.join('media', 'templates', 'demos', filename)
            
            if os.path.exists(correct_path):
                print(f"  Found file in correct location: {correct_path}")
                # Update the database to point to the correct path
                template.demo_video.name = f"templates/demos/{filename}"
                template.save()
                print(f"  Updated database path for template {template.id}")
            else:
                print(f"  File not found in either location for template {template.id}")

if __name__ == "__main__":
    fix_demo_paths()
