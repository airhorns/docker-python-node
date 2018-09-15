from jinja2 import Environment, FileSystemLoader
import itertools
import shutil
import yaml
import os

current_directory = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(current_directory, 'config.yml'), 'r') as f:
    config = yaml.load(f)

env = Environment(loader=FileSystemLoader(os.path.join(current_directory, 'templates')))
env.filters['dirname'] = os.path.dirname
env.filters['monospaced_list'] = lambda items: ", ".join(map(lambda item: f'`{item}`', items))

destination_directory = os.path.join(current_directory, 'dockerfiles')
hyphenize = lambda item: f"-{item}"


def tag(python_version, node_version, base):
    return f'{python_version}-{node_version}-{base}';


def alias_tags(python_aliases, node_aliases, base, base_properties):
    base_aliases = base_properties.get('aliases', []).copy()
    base_aliases.append(base)
    base_aliases = list(map(hyphenize, base_aliases))
    if base_properties.get('default', False):
        base_aliases.append("")

    return list(map(
        "".join,
        itertools.product(python_aliases, map(hyphenize, node_aliases), base_aliases)
    ))


def reset_output():
    shutil.rmtree(destination_directory)
    os.makedirs(destination_directory)


def write_dockerfile(build):
    directory = os.path.dirname(os.path.join(current_directory, 'dockerfiles', build['filename']))
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(current_directory, 'dockerfiles', build['filename']), 'w') as f:
        f.write(env.get_template(f"{ base_properties['template_name'] }.jinja2").render(**build))

    print(f"Generated {build['filename']}")


def write_circleconfig(builds):
    unique_tags = set()
    for build in builds:
        if build['tag'] in unique_tags:
            raise f"Duplicate tag found: {build['tag']} !"
        else:
            unique_tags.add(build['tag'])

        for alias_tag in build['alias_tags']:
            if alias_tag in unique_tags:
                raise f"Duplicate tag found: {alias_tag} !"
            else:
                unique_tags.add(alias_tag)


    circle_template = env.get_template('circleci-config.yml.jinja2')
    with open(os.path.join(current_directory, '.circleci', 'config.yml'), 'w') as f:
        f.write(circle_template.render(config=config, builds=builds))
        print(f'Generated circleci config')


def write_readme(builds):
    readme_template = env.get_template('Readme.md.jinja2')
    with open(os.path.join(current_directory, 'Readme.md'), 'w') as f:
        f.write(readme_template.render(config=config, builds=builds))
        print(f'Generated Readme')


reset_output()
builds = []

for base, base_properties in config['bases'].items():
    for python_version, python_properties in config['python_versions'].items():
        for node_version, node_properties in config['node_versions'].items():
            build_tag = tag(python_version, node_version, base)
            build = {
                'filename': f'{build_tag}/Dockerfile',
                'image_name': config['image_name'],
                'tag': f'{build_tag}',
                'python_version': python_version,
                'node_version': node_version,
                'base': base,
                'alias_tags': alias_tags(python_properties['aliases'], node_properties['aliases'], base, base_properties)
            }

            builds.append(build)
            write_dockerfile(build)


write_circleconfig(builds)
write_readme(builds)
