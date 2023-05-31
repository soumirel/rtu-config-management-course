import graphviz
import requests


def form_graph(package_name, current_depth=0):
    if current_depth < __depth:
        current_depth += 1

        package_url = 'https://pypi.python.org/pypi/' + str(package_name) + '/json'
        package_json = requests.get(package_url).json()
        if 'message' in package_json:
            raise Exception(package_json['message'])

        requires_dist = package_json['info']['requires_dist']

        if requires_dist:
            dependencies = [str(x).split(' ')[0]
                            .split('>')[0]
                            .split('<')[0]
                            .split('[')[0]
                            .split('=')[0]
                            .replace(';', '')
                            .replace('!', '')
                            .replace('-', '_')
                            .replace('.', '_') for x in requires_dist]

            for dependency in dependencies:
                if package_name not in existing_dependencies:
                    existing_dependencies[package_name] = []
                if dependency not in existing_dependencies[package_name]:
                    existing_dependencies[package_name].append(dependency)
                    graphviz_graph.edge(package_name, dependency)
                    print(graphviz_graph.body[len(graphviz_graph.body) - 1], end='')
                form_graph(dependency, current_depth)


if __name__ == "__main__":

    __depth = 0
    is_correct_choice = False
    while not is_correct_choice:
        try:
            __depth = int(input('Введите глубину поиска зависимостей: '))
            if __depth <= 0:
                raise ValueError
            is_correct_choice = True
        except ValueError as value_error:
            print('Ожидалось натуральное число')

    __package_name = input('Введите имя пакета: ')

    graphviz_graph = graphviz.Digraph(comment='Зависимости пакета ' + __package_name)

    try:
        existing_dependencies = {}
        __dependencies = {__package_name: form_graph(__package_name)}
        print('Отобразить зависимости в виде графа?\nДа - 1, Нет - 0')
        if input() == '1':
            graphviz_graph.render((__package_name + "_dependencies"), view=True)
    except Exception as exception:
        print("Произошла ошибка: " + str(exception))
