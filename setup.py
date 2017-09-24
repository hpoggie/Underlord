from setuptools import setup

setup(
    name="Overlord",
    options={
        'build_apps': {
            'copy_paths': [
                '.',
                'templar_icons',
            ],
            'exclude_paths': [
                'build/*',
                'setup.py',
                'requirements.txt',
                'wheels/*',
                '*.swp',
                'tests/*',
                '.git/*',
                '.gitignore'
            ],
            'plugins': [
                'pandagl',
            ],
            'gui_apps': {
                'Overlord': 'client.py',
            },
            'deploy_platforms': [
                'manylinux1_x86_64',  # 108
                # 'macosx_10_6_x86_64',
                # 'win32',
                'win_amd64',  # 104
            ],
        }
    },
    packages=['core', 'factions']
)
