from glob import glob
from inspect import signature

import aug

from cvlab.diagram.elements import add_plugin_callback
from cvlab.diagram.elements.base import *
from cvlab_samples import get_menu, OpenExampleAction


class AugBaseElement(NormalElement):
    name = "Base element for aug library"
    comment = "Base element for aug library"
    package = "Augmentation"
    operation = aug.Operation

    def __init__(self):
        super().__init__()

    def get_operation(self, parameters):
        for parameter in parameters:
            if isinstance(parameters, tuple):
                parameters[parameter] = aug.uniform(*parameter)

        return self.operation(**parameters)

    def get_params(self):
        all_params = []

        def decode_param(param):
            if param.name in ("self", "args", "kwargs"):
                return
            if param.name == "p":
                all_params.append(FloatParameter("p", value=1, min_=0, max_=1))
            else:
                if isinstance(param.default, tuple):
                    count = len(param.default)
                    param_type = type(param.default[0])
                else:
                    count = 1
                    param_type = type(param.default)

                if count == 1 and param_type == int:
                    all_params.append(IntParameter(param.name, value=param.default))
                elif count == 1 and param_type == float:
                    all_params.append(FloatParameter(param.name, value=param.default))
                elif count == 2 and param_type == int:
                    all_params.append(SizeParameter(param.name, value=param.default))
                elif count == 2 and param_type == float:
                    all_params.append(TwoFloatsParameter(param.name, value=param.default))
                elif count == 4 and param_type == float:
                    all_params.append(ScalarParameter(param.name, value=param.default))

        for param in signature(self.operation).parameters.values():
            decode_param(param)

        if hasattr(self.operation, "cls"):
            operation = self.operation().cls
            for param in signature(operation).parameters.values():
                decode_param(param)

        return all_params

    def get_attributes(self):
        return [Input("input", name="Input")], \
               [Output("output", name="Output")], \
               [ButtonParameter("", self.apply, "Apply")] + self.get_params()

    def process_inputs(self, inputs, outputs, parameters):
        if "" in parameters: parameters.pop("")
        image = inputs["input"].value.copy()
        image = self.get_operation(parameters).apply_on_image(image)
        outputs["output"] = Data(image)

    def apply(self):
        self.recalculate(True,False,True,False)


def create_aug_element(name, operation):
    element = type("Aug" + name, (AugBaseElement,), {
        "name": name,
        "operation": operation,
    })
    globals()[name] = element
    return element


def create_aug_elements():
    ignored = ["Operation"]
    elements = []

    for name, var in vars(aug).items():
        if name in ignored: continue
        if isinstance(var, type) and issubclass(var, (aug.Operation, aug.BaseWrapper)):
            element = create_aug_element(name, var)
            elements.append(element)

    register_elements("Augmentation", elements, 5)


def add_samples(main_window):
    samples = glob(os.path.dirname(__file__) + "/*.cvlab")
    samples.sort()

    print("Adding {} sample diagrams to 'Examples/Augmentation' menu".format(len(samples)))

    menu = get_menu(main_window, 'Examples/Augmentation')

    for sample in samples:
        menu.addAction(OpenExampleAction(main_window, sample))


create_aug_elements()
add_plugin_callback(add_samples)

