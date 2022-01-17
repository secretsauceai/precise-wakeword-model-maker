from traceback import print_exc
from wake_word_data_prep_classes import BasicFileOperations, PreciseModelingOperations
from get_base_model_flow import incremental_training_flow
from get_base_model_flow import train_model_flow

basic_file_operations_instance = BasicFileOperations()
precise_modeling_operations_instance = PreciseModelingOperations()

# TODO: test this
# TODO: input for flow to add one or multiple directories (make list of datasets and links for IDE)
# TODO: refactor the code to use the basic_file_operations_instance more (the problem is either copying wav or converting to mp3 and then copying to wav)


def convert_mp3s_to_wavs_split_into_multiple_directories(
    source_directory,
    destination_directory,
    max_files_from_source_directory,
    max_files_per_destination_directory,
):
    files = basic_file_operations_instance.get_limited_number_of_files(
        source_directory, max_files_from_source_directory
    )
    print(f"{len(files)} files found in {source_directory}")
    directory_number = 1
    file_count = 1
    number_of_directories = int(len(files) / max_files_per_destination_directory) + 1

    def check_for_wav_files(files, source_directory):
        if all(file.endswith(".wav") for file in files):
            print(f"All files in {source_directory} are already in wav format")
            return True
        else:
            print(
                f"All files in {source_directory} are probably in mp3 format and will be converted to wav"
            )
            return False

    check_for_wav_files = check_for_wav_files(files, source_directory)

    def split_files_into_multiple_directories(
        files, directory_number, file_count, number_of_directories
    ):
        # Will copy if files are already in wav format, otherwise will convert to wav and then copy
        for file in files:
            if number_of_directories > 1:
                # print(f'Number of directories: {number_of_directories}')
                destination_slug = "0" + str(directory_number) + "/"
                basic_file_operations_instance.make_directory(
                    destination_directory + destination_slug
                )
            else:
                destination_slug = ""
            if file_count < max_files_per_destination_directory:
                if check_for_wav_files:
                    basic_file_operations_instance.copy_file(
                        file, source_directory, destination_directory + destination_slug
                    )
                else:
                    basic_file_operations_instance.convert_mp3_to_wav(
                        file, source_directory, destination_directory + destination_slug
                    )
                file_count += 1
            elif file_count == max_files_per_destination_directory:
                if check_for_wav_files:
                    basic_file_operations_instance.copy_file(
                        file, source_directory, destination_directory + destination_slug
                    )
                else:
                    basic_file_operations_instance.convert_mp3_to_wav(
                        file, source_directory, destination_directory + destination_slug
                    )
                directory_number += 1
                file_count = 1
        return number_of_directories

    return split_files_into_multiple_directories(
        files, directory_number, file_count, number_of_directories
    )


def incremental_train_over_number_of_directories(
    number_of_directories, wakeword_model_name, destination_directory
):
    if number_of_directories > 1:
        for directory_number in range(1, number_of_directories + 1):
            current_model_info = incremental_training_flow(
                destination_directory + "0" + str(directory_number) + "/",
                wakeword_model_name,
                epochs="10",
            )
    else:
        current_model_info = incremental_training_flow(
            destination_directory, wakeword_model_name, epochs="20"
        )
    print(f"Current model info: {current_model_info}")
    return current_model_info


def further_data_generation_flow(
    directories_to_process,
    extra_audio_directories_labels,
    max_files_from_source_directory,
    max_files_per_destination_directory,
    wakeword_model_name,
):
    for source_directory, extra_audio_directories_label in zip(
        directories_to_process, extra_audio_directories_labels
    ):
        destination_directory = (
            "out/"
            + wakeword_model_name
            + "/"
            + "random/"
            + extra_audio_directories_label
            + "/"
            + source_directory.split("/")[-2]
            + "/"
        )

        basic_file_operations_instance.make_directory(destination_directory)
        number_of_directories = convert_mp3s_to_wavs_split_into_multiple_directories(
            source_directory,
            destination_directory,
            max_files_from_source_directory,
            max_files_per_destination_directory,
        )
        print(
            f"All files from {source_directory} have been copied to {destination_directory}"
        )

        current_model_info = incremental_train_over_number_of_directories(
            number_of_directories, wakeword_model_name, destination_directory
        )

        print(f"Training complete for {source_directory}")
        print(f"Current model info: {current_model_info}")

    final_model_info = train_model_flow(wakeword_model_name, epochs="50")

    print("Final training complete")
    # TODO: get number of epochs from the model info
    # TODO: train a model on the whole dataset with the same number of epochs as the last model
    # TODO: compare the results (done by hand: about 10% increase in accuracy on test set, not bad!)
    print(f"Final model info: {final_model_info}")
    print(f"Make sure to test your model in precise-listen {wakeword_model_name}.net")


# TESTING:


"""
wakeword_model_name = 'test_wakeword_model_delete_after'
extra_audio_directories_label = 'non_utterance'
source_directory = 'jarvis_S_B_remixed/random/other/non-utterances/noises/'

destination_directory = wakeword_model_name + '/' + 'random/' + extra_audio_directories_label + '/' + source_directory.rsplit('/', 2)[-2]
print(destination_directory)
"""

# DEBUG:
# TODO: only the first file is copied, need to fix this

"""max_files_from_source_directory = 45000
max_files_per_destination_directory = 10000

files = basic_file_operations_instance.get_limited_number_of_files(source_directory, max_files_from_source_directory)
print(f'{len(files)} files found in {source_directory}')
directory_number = 1
file_count = 1
number_of_directories = int(len(files) / max_files_per_destination_directory) + 1
print(f'{number_of_directories} directories will be created')"""
