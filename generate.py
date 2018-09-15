from jinja2 import Environment, FileSystemLoader
import shutil
import yaml
import os

current_directory = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(current_directory, 'config.yml'), 'r') as f:
    config = yaml.load(f)

env = Environment(loader=FileSystemLoader(os.path.join(current_directory, 'templates')))
env.filters['dirname'] = os.path.dirname
destination_directory = os.path.join(current_directory, 'dockerfiles')

shutil.rmtree(destination_directory)
os.makedirs(destination_directory)

builds = []

for base, base_properties in config['bases'].items():
    for python_version in config['python_versions']:
        for node_version in config['node_versions']:
            build = {
                'filename': f'{python_version}-{node_version}-{base}/Dockerfile',
                'tag': f'airhorns/python-node:{python_version}-{node_version}-{base}',
                'python_version': python_version,
                'node_version': node_version,
                'base': base,
                'alias_tags': []
            }

            builds.append(build)

            directory = os.path.dirname(os.path.join(current_directory, 'dockerfiles', build['filename']))
            if not os.path.exists(directory):
                os.makedirs(directory)

            with open(os.path.join(current_directory, 'dockerfiles', build['filename']), 'w') as f:
                f.write(env.get_template(f"{ base_properties['template_name'] }.jinja2").render(**build))

            print(f"Generated {build['filename']}")

circle_template = env.get_template('circleci-config.yml.jinja2')
with open(os.path.join(current_directory, '.circleci', 'config.yml'), 'w') as f:
    f.write(circle_template.render(config=config, builds=builds))
    print(f'Generated circleci config')
