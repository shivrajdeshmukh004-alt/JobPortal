from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Split a string by the given separator"""
    if value:
        return value.split(arg)
    return []

@register.filter(name='strip')
def strip(value):
    """Strip whitespace from a string"""
    if value:
        return value.strip()
    return value

@register.filter(name='get_list')
def get_list(dictionary, key):
    """Get a list of values from a query dict by key"""
    return dictionary.getlist(key)

@register.filter(name='select_if')
def select_if(value, arg):
    """Return 'selected' if value == arg"""
    if str(value) == str(arg):
        return 'selected'
    return ''

@register.filter(name='format_projects')
def format_projects(projects):
    """Format projects JSON field for display"""
    if not projects:
        return "No details provided."
    
    if isinstance(projects, list):
        # Extract project names/titles from the list of dicts
        project_names = []
        for project in projects:
            if isinstance(project, dict):
                name = project.get('name') or project.get('title') or project.get('project_name')
                if name:
                    project_names.append(name)
            elif isinstance(project, str):
                project_names.append(project)
        
        if project_names:
            return ', '.join(project_names[:3])  # Show first 3 projects
        return "No details provided."
    
    return str(projects)
