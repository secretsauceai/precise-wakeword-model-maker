from wake_word_data_prep_classes import (
    BasicFileOperations,
    TrainTestSplit,
    PreciseModelingOperations,
)
import os
from dialog_handler import DialogHandler

train_test_split_instance = TrainTestSplit()
precise_modeling_operations_instance = PreciseModelingOperations()
basic_file_operations_instance = BasicFileOperations()

dialog_name = "base_model_menu_dialog"
dialog_handler_instance = DialogHandler("dialog.json", dialog_name)


# Get base model
def move_random_user_collection(source_directory):

    # NOTE: I had to change this function back to similar to the original, otherwise the user collected random data wasn't being copied over to the new directory
    random_source_directory = basic_file_operations_instance.get_sub_directory(
        source_directory, "random"
    )
    random_destination_directory = random_source_directory + "user_collected/"

    if not os.path.exists(random_destination_directory):
        files = basic_file_operations_instance.get_files(random_source_directory)
        basic_file_operations_instance.copy_directory(
            files, random_source_directory, random_destination_directory
        )
        basic_file_operations_instance.delete_files_in_directory(
            files, random_source_directory
        )

    return random_destination_directory


def split_data_and_get_best_model_flow(
    source_directory,
    random_split_directories,
    even_odd_split_directories,
    three_four_split_directories,
    root_model_name,
):
    print(
        dialog_handler_instance.render_template(
            "inform-splitting_data", source_directory=source_directory
        )
    )
    model_names = train_test_split_instance.experimental_splits(
        source_directory,
        random_split_directories,
        even_odd_split_directories,
        three_four_split_directories,
        root_model_name,
    )

    print(dialog_handler_instance.render_template("inform-experiment_train_test_split"))
    models = precise_modeling_operations_instance.run_experimental_training(model_names)
    (
        average_acc_for_min_loss_models,
        stdev_acc_for_min_loss_models,
        average_val_acc_for_min_loss_models,
        stdev_val_acc_for_min_loss_models,
    ) = precise_modeling_operations_instance.get_optimal_training_model_analytics()
    # for val_loss selection: average_val_acc, standard_deviation_val_acc, average_acc, standard_deviation_acc = precise_modeling_operations_instance.get_optiomal_testing_model_analytics()
    experimental_average_accuracy_dialog = dialog_handler_instance.render_template(
        "inform-accuracy",
        average_val_acc=average_val_acc_for_min_loss_models,
        standard_deviation_val_acc=stdev_val_acc_for_min_loss_models,
        average_acc=average_acc_for_min_loss_models,
        standard_deviation_acc=stdev_acc_for_min_loss_models,
    )

    print(experimental_average_accuracy_dialog)

    (
        best_training_set_accuracy_model_name,
        best_training_set_accuracy_model,
    ) = precise_modeling_operations_instance.get_best_loss_model()
    selected_model_name = best_training_set_accuracy_model_name
    selected_model_results = best_training_set_accuracy_model[0]
    dataset_size = best_training_set_accuracy_model[2]
    experimental_average_accuracy_dialog = dialog_handler_instance.render_template(
        "inform-best_model",
        selected_model_name=selected_model_name,
        selected_model_results=selected_model_results,
    )

    return (
        selected_model_name,
        selected_model_results,
        dataset_size,
        experimental_average_accuracy_dialog,
    )


def train_model_flow(wakeword_model_name, epochs=None):
    print(
        dialog_handler_instance.render_template(
            "inform-training_start", wakeword_model_name=wakeword_model_name
        )
    )
    training_run = precise_modeling_operations_instance.run_precise_train(
        wakeword_model_name, epochs
    )
    print(
        dialog_handler_instance.render_template(
            "inform-training_complete", wakeword_model_name=wakeword_model_name
        )
    )

    precise_modeling_operations_instance.get_model_info(
        wakeword_model_name, training_run
    )

    return precise_modeling_operations_instance.models[wakeword_model_name]


def incremental_training_flow(
    random_user_recordings_directory, selected_model_name, epochs=None
):
    # TODO: add CLI elements into class?
    print(
        dialog_handler_instance.render_template(
            "inform-incremental_training_start",
            random_user_recordings_directory=random_user_recordings_directory,
        )
    )
    precise_modeling_operations_instance.incremental_training(
        selected_model_name, random_user_recordings_directory
    )
    print(
        dialog_handler_instance.render_template(
            "inform-incremental_training_complete",
            random_user_recordings_directory=random_user_recordings_directory,
        )
    )

    train_test_split_instance.split_incremental_results(selected_model_name)

    precise_modeling_operations_instance.delete_generated_directories(
        selected_model_name
    )
    precise_modeling_operations_instance.delete_model(selected_model_name + "_tmp_copy")

    model_info = train_model_flow(selected_model_name, epochs)

    return model_info


def get_base_model_flow(
    source_directory,
    random_split_directories,
    even_odd_split_directories,
    three_four_split_directories,
    root_model_name,
    wakeword_model_name,
):
    random_user_recordings_directory = move_random_user_collection(source_directory)

    (
        selected_model_name,
        selected_model_results,
        selected_model_dataset_size,
        experimental_average_accuracy_dialog,
    ) = split_data_and_get_best_model_flow(
        source_directory,
        random_split_directories,
        even_odd_split_directories,
        three_four_split_directories,
        root_model_name,
    )

    precise_modeling_operations_instance.delete_experiment_directories(
        selected_model_name
    )

    base_model_info = incremental_training_flow(
        random_user_recordings_directory, selected_model_name, epochs="50"
    )

    precise_modeling_operations_instance.delete_experiment_models(selected_model_name)
    precise_modeling_operations_instance.rename_model(
        selected_model_name, wakeword_model_name
    )
    basic_file_operations_instance.rename_directory(
        "out/" + selected_model_name, "out/" + wakeword_model_name
    )
    print(
        dialog_handler_instance.render_template(
            "inform-changed_model_name",
            selected_model_name=selected_model_name,
            wakeword_model_name=wakeword_model_name,
        )
    )

    print(dialog_handler_instance.render_template("inform-base_model_accuracies"))
    print(experimental_average_accuracy_dialog)

    print(
        dialog_handler_instance.render_template(
            "inform-original_best_base_model_results",
            selected_model_name=selected_model_name,
            selected_model_results=selected_model_results,
            dataset_size=selected_model_dataset_size,
        )
    )
    print(
        f"Current base model with incremental training on your random audio recordings:\n {wakeword_model_name}: {base_model_info[0]} \n dataset size: {base_model_info[2]}"
    )
    print(
        f"Not bad when you consider the average accuracies of the first base model..."
    )

    print(
        dialog_handler_instance.render_template(
            "inform-continue", wakeword_model_name=wakeword_model_name
        )
    )

    return base_model_info


# test stuff
# TODO: move to test file
# 1. get_base_model_flow configuration
"""
source_directory = 'flow_test_delete_after'

random_split_directories = [
    '/wake-word/',
    '/not-wake-word/background/'
]

even_odd_split_directories = [
    '/wake-word/variations/'
]

three_four_split_directories = [
    '/not-wake-word/parts/'
]

root_model_name = 'experiment'

destination_directory = 'file_split_test/'
"""

# train_test_split_instance.experimental_splits(source_directory, random_split_directories, even_odd_split_directories, three_four_split_directories, root_model_name)

# train model and incremental training flow configuration
"""
wakeword_model_name = 'test_wakeword_model_delete_after'
noise_destination_directory = wakeword_model_name + '/random/non-utterances/pdsounds_march2009/'
model_info = train_model_flow(wakeword_model_name, epochs)
print(model_info)
model_info = incremental_training_flow(noise_destination_directory, wakeword_model_name)
print(model_info)"""

"""import json

with open('data_prep_user_configuration.json', 'r') as file:
    user_configuration_dictionary = json.load(file)
source_directory = user_configuration_dictionary['audio_source_directory']
wakeword_model_name = user_configuration_dictionary['wakeword_model_name']
pdsounds_directory = user_configuration_dictionary['pdsounds_directory']
directories_to_process = user_configuration_dictionary['extra_audio_directories_to_process']
extra_audio_directories_labels = user_configuration_dictionary['extra_audio_directories_labels']
max_files_from_source_directory = user_configuration_dictionary['max_files_from_source_directory']
max_files_per_destination_directory = user_configuration_dictionary['max_files_per_destination_directory']


with open('data_prep_system_configuration.json', 'r') as file:
    system_configuration_dictionary = json.load(file)    
random_split_directories = system_configuration_dictionary['random_split_directories']
even_odd_split_directories = system_configuration_dictionary['even_odd_split_directories']
three_four_split_directories = system_configuration_dictionary['three_four_split_directories']
root_model_name = system_configuration_dictionary['root_model_name']
source_directories = system_configuration_dictionary['source_directories']
destination_directories = system_configuration_dictionary['destination_directories']
directories_to_gauss = system_configuration_dictionary['directories_to_gauss']

best_training_set_accuracy_model = split_data_and_get_best_model_flow(source_directory, random_split_directories, even_odd_split_directories, three_four_split_directories, root_model_name)
#print(best_training_set_accuracy_model)
print(best_training_set_accuracy_model)"""


"""
changed experiment_4 to test_wakeword_model_delete_after
Average accuracies of the base model...
experiment_4 produces the best results with {'minimum_loss_val_accuracy': {'epoch': 49, 'loss': 0.1925, 'acc': 0.6705, 'val_loss': 0.1503, 'val_acc': 0.6949, 'acc_difference': 0.024399999999999977}}
Original best model: {'minimum_loss_val_accuracy': {'epoch': 49, 'loss': 0.1925, 'acc': 0.6705, 'val_loss': 0.1503, 'val_acc': 0.6949, 'acc_difference': 0.024399999999999977}}
Current base model with incremental training on your random audio recordings: {'acc': 0.6878, 'val_acc': 0.6901, 'difference': 0.0023000000000000798}
Not bad when you consider the average accuracies of the first base model...
"""
