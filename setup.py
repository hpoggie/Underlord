from setuptools import setup

setup(
    name="Underlord",
    options={
        'build_apps': {
            'exclude_modules': [
                'GitPython'
            ],
            'include_patterns': [
                '*.png',
                '*.ttf',
                'CREDITS.txt'
            ],
            'plugins': [
                'pandagl',
            ],
            'gui_apps': {
                'Underlord': 'client/__main__.py',
            },
            'platforms': [
                'manylinux1_x86_64',
                # 'macosx_10_6_x86_64',
                # 'win32',
                'win_amd64',
            ],
        }
    },
)
