import random
import os
from os import listdir, mkdir
from os.path import isfile, isdir, join
import shutil
from numpy.lib.function_base import copy
from pydub import AudioSegment


import subprocess
import statistics

import numpy as np
from scipy.io import wavfile

from model_analytics import ModelAnalytics

# TODO: split up the classes into separate files
# TODO: refactor classes


class BasicFileOperations:
    @staticmethod
    def get_files(source_directory):
        return [
            f for f in listdir(source_directory) if isfile(join(source_directory, f))
        ]

    def get_number_of_files(self, source_directory):
        if not source_directory.endswith("/"):
            source_directory += "/"
        return len(self.get_files(source_directory))

    def get_limited_number_of_files(self, source_directory, max_number_of_files):
        max_number_of_files -= 1
        files = [
            f
            for f in listdir(source_directory)[:max_number_of_files]
            if isfile(join(source_directory, f))
        ]
        return files

    @staticmethod
    def copy_file(file, source_directory, destination_directory):
        try:
            shutil.copyfile(source_directory + file, destination_directory + file)
        except:
            print(f"Error with {file}")

    @staticmethod
    def rename_file(old_filename, new_filename, directory=None):
        try:
            if directory:
                os.rename(directory + old_filename, directory + new_filename)
            else:
                os.rename(old_filename, new_filename)
        except:
            print(f"Error with {old_filename}")

    def backup_file(self, source_file, destination_file, source_directory=None):
        # This will rename a file in a directory
        # It will also copy the file to the destination directory
        try:
            if source_directory:
                shutil.copyfile(
                    source_directory + source_file, source_directory + destination_file
                )
            else:
                shutil.copyfile(source_file, destination_file)
        except:
            print(f"Error with {source_file}")

    @staticmethod
    def dir_str(directory):
        if not directory.endswith("/"):
            directory += "/"
        return directory

    def get_sub_directory(self, source_directory, sub_directory):
        return self.dir_str(source_directory) + self.dir_str(sub_directory)

    @staticmethod
    def make_directory(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def copy_directory(self, files, source_directory, destination_directory):
        self.make_directory(destination_directory)
        for file in files:
            try:
                shutil.copyfile(source_directory + file, destination_directory + file)
            except:
                pass

    def create_directory(self, source_directory, sub_directory):

        self.make_directory(
            self.dir_str(source_directory) + self.dir_str(sub_directory)
        )
        return source_directory + sub_directory

    @staticmethod
    def delete_directory(directory):
        if os.path.exists(directory):
            print(f"Deleting {directory}")
            shutil.rmtree(directory)
        else:
            print(f"Directory {directory} does not exist")

    @staticmethod
    def delete_file(file):
        if os.path.exists(file):
            print(f"Removing {file}")
            os.remove(file)
        else:
            print(f"File {file} does not exist")

    def delete_files_in_directory(self, files, directory):
        for file in files:
            self.delete_file(directory + file)

    @staticmethod
    def rename_directory(source_directory, destination_directory):
        if os.path.exists(destination_directory):
            # TODO: input from user to continue
            print(f"Directory {destination_directory} already exists")
        else:
            if os.path.exists(source_directory):
                os.rename(source_directory, destination_directory)
                print(
                    f"Directory {source_directory} renamed to {destination_directory}"
                )
            else:
                print(f"Directory {source_directory} does not exist")

    @staticmethod
    def read_wave_file(file):
        if file.endswith(".wav"):
            try:
                sample_frequency, wave_data = wavfile.read(file)
                return sample_frequency, wave_data
            except:
                print(f"Error with {file}")

    @staticmethod
    def write_wave_file(file, sample_frequency, data):
        wavfile.write(file, sample_frequency, data)

    def convert_mp3_to_wav(self, file, source_directory, destination_directory):
        # ensure source directory ends with a /
        if not source_directory.endswith("/"):
            source_directory += "/"
        if file.endswith(".mp3"):
            try:
                sound = AudioSegment.from_file(source_directory + file)
                sound = sound.set_frame_rate(16000)
                sound = sound.set_channels(1)
                wav_file_name = file.replace(".mp3", ".wav")
                self.make_directory(destination_directory)
                sound.export(destination_directory + wav_file_name, format="wav")
            except Exception as e:
                print(f"Error with {file}")
                print(destination_directory)
                print(e)

    def convert_mp3s_in_directory_to_wavs(
        self, source_directory, destination_directory
    ):
        files = self.get_files(source_directory)
        self.make_directory(destination_directory)
        # NOTE: you definitely want the directory to be updated
        # here rather than on each call to convert_mp3_to_wav
        # but still want to check if convert_mp3_to_wav is intented to be
        # used by itself on occasion
        if not source_directory.endswith("/"):
            source_directory += "/"
        if all(file.endswith(".wav") for file in files):
            print("All files are already in wav format")
        else:
            print(f"Converting {len(files)} mp3 files to wav")
            for file in files:
                self.convert_mp3_to_wav(file, source_directory, destination_directory)
            print("Conversion complete")

    def change_sample_rate_of_wav_file(
        self, file, source_directory, destination_directory
    ):
        # This will take a wav file and change the sample rate to 16000
        if file.endswith(".wav"):
            try:  # TODO: make a function that returns the model analytics
                if sound.frame_rate != 16000:
                    sound = sound.set_frame_rate(16000)
                    sound = sound.set_channels(1)
                    sound.export(destination_directory + file, format="wav")
                    return True
                else:
                    return False
            except:
                print(f"Error with {file}")
                return False

    def change_sample_rate_of_wavs_in_directory(
        self, source_directory, destination_directory
    ):
        print(
            "This will also copy all files already in 16000 sample rate into the destination directory"
        )
        files = self.get_files(source_directory)
        self.make_directory(destination_directory)
        for file in files:
            converted = self.change_sample_rate_of_wav_file(
                file, source_directory, destination_directory
            )
            if not converted:
                self.copy_file(file, source_directory, destination_directory)

    def split_files_into_multiple_directories(
        self,
        files,
        number_of_files_per_directory,
        source_directory,
        destination_directory,
    ):
        # This will take a directory with a huge amount of files and break them down into smaller directories
        # It can have a max number of files (might have to refactor get_files for getting only a max number)
        directory_number = 1
        file_count = 1
        for file in files:
            if file_count < number_of_files_per_directory:
                self.copy_file(
                    file,
                    source_directory,
                    destination_directory + "_0" + str(directory_number),
                )
                file_count += 1
            elif file_count == number_of_files_per_directory:
                self.copy_file(
                    file,
                    source_directory,
                    destination_directory + "_0" + str(directory_number),
                )
                directory_number += 1
                file_count = 1


class TrainTestSplit:
    @staticmethod
    def random_training_test_split(files, dataset_percent_size):
        random_selected_training_files = random.sample(
            files, int(len(files) * dataset_percent_size)
        )
        random_selected_testing_files = [
            file for file in files if file not in random_selected_training_files
        ]
        return random_selected_training_files, random_selected_testing_files

    @staticmethod
    def even_odd_training_test_split(files):
        selected_training_files = []
        selected_testing_files = []
        for file in files:
            file_number = int(file.split("_")[-1].replace(".wav", ""))
            if (file_number % 2) == 0:
                selected_training_files.append(file)
            else:
                selected_testing_files.append(file)
        return selected_training_files, selected_testing_files

    @staticmethod
    def three_four_training_test_split(files):
        selected_training_files = []
        selected_testing_files = []
        count = 0
        for file in files:
            # TODO: add in this instead for final version file_number = int(file.split('_')[-1].replace('.wav', ''))
            if count < 3:
                selected_training_files.append(file)
                count = count + 1
            else:
                selected_testing_files.append(file)
                count = 0
        return selected_training_files, selected_testing_files

    def split_directory(
        self, source_directory, training_directory, testing_directory, split_type
    ):
        dataset_percent_size = float(0.8)
        if not source_directory.endswith("/"):
            source_directory += "/"
        # function to split one directory and output the test and training directories
        # pass split_type to use either random or even_odd
        basic_file_operations_instance = BasicFileOperations()
        files = basic_file_operations_instance.get_files(source_directory)
        if split_type is "random":
            (
                random_selected_training_files,
                random_selected_testing_files,
            ) = self.random_training_test_split(files, dataset_percent_size)
            basic_file_operations_instance.copy_directory(
                random_selected_training_files, source_directory, training_directory
            )
            basic_file_operations_instance.copy_directory(
                random_selected_testing_files, source_directory, testing_directory
            )
        if split_type is "even_odd":
            (
                random_selected_training_files,
                random_selected_testing_files,
            ) = self.even_odd_training_test_split(files)
            basic_file_operations_instance.copy_directory(
                random_selected_training_files, source_directory, training_directory
            )
            basic_file_operations_instance.copy_directory(
                random_selected_testing_files, source_directory, testing_directory
            )
        if split_type is "three_four":
            (
                random_selected_training_files,
                random_selected_testing_files,
            ) = self.three_four_training_test_split(files)
            basic_file_operations_instance.copy_directory(
                random_selected_training_files, source_directory, training_directory
            )
            basic_file_operations_instance.copy_directory(
                random_selected_testing_files, source_directory, testing_directory
            )

    def split_multiple_directories(
        self,
        source_directory,
        destination_directory,
        random_split_directories,
        even_odd_split_directories,
        three_four_split_directories,
    ):
        sub_directories = (
            random_split_directories
            + even_odd_split_directories
            + three_four_split_directories
        )
        for sub_directory in sub_directories:
            training_directory = destination_directory + sub_directory
            testing_directory = destination_directory + "test/" + sub_directory
            for random_split_directory in random_split_directories:
                if sub_directory is random_split_directory:
                    split_type = "random"
                    self.split_directory(
                        source_directory + sub_directory,
                        training_directory,
                        testing_directory,
                        split_type,
                    )
            for even_odd_split_directory in even_odd_split_directories:
                if sub_directory is even_odd_split_directory:
                    split_type = "even_odd"
                    self.split_directory(
                        source_directory + sub_directory,
                        training_directory,
                        testing_directory,
                        split_type,
                    )
            for three_four_split_directory in three_four_split_directories:
                if sub_directory is three_four_split_directory:
                    split_type = "three_four"
                    self.split_directory(
                        source_directory + sub_directory,
                        training_directory,
                        testing_directory,
                        split_type,
                    )

    def experimental_splits(
        self,
        source_directory,
        random_split_directories,
        even_odd_split_directories,
        three_four_split_directories,
        root_model_name,
    ):
        # This will run when the user selects the default action to randomly perform
        # TODO: test-train-splitting 5 times to obtain the best data distribution: Perhaps 10 to be sure?
        model_names = [root_model_name + "_" + str(i + 1) for i in range(10)]
        if not isdir("out"):
            mkdir("out")
        for model in model_names:
            destination_directory = "out/" + model + "/"
            self.split_multiple_directories(
                source_directory,
                destination_directory,
                random_split_directories,
                even_odd_split_directories,
                three_four_split_directories,
            )
        return model_names

    def split_incremental_results(self, model_name):
        # TODO: This really needs to be split up!

        files = []
        dataset_percent_size = float(0.8)
        source_directories = [
            "out/" + model_name + "/not-wake-word/generated/",
            "out/" + model_name + "/test/not-wake-word/generated/",
        ]

        training_directory = "out/" + model_name + "/not-wake-word/random/"
        testing_directory = "out/" + model_name + "/test/not-wake-word/random/"

        basic_file_operations_instance = BasicFileOperations()

        for source_directory in source_directories:
            files += basic_file_operations_instance.get_files(source_directory)
        # TODO: Need to go through again to copy and delete
        (
            random_selected_training_files,
            random_selected_testing_files,
        ) = self.random_training_test_split(files, dataset_percent_size)
        for source_directory in source_directories:
            basic_file_operations_instance.copy_directory(
                random_selected_training_files, source_directory, training_directory
            )
            basic_file_operations_instance.copy_directory(
                random_selected_testing_files, source_directory, testing_directory
            )
        print(
            "Finished spliting all files in generated test and training to random test and training directories"
        )


class PreciseModelingOperations:
    def __init__(self):
        self.model_analytics_instance = ModelAnalytics()
        self.models = self.model_analytics_instance.models

    @staticmethod
    def run_precise_train(model_name, epochs=None, source_directory=None):
        # TODO: better code for subprocess? What about closing when done? Should I use 'with'?

        if source_directory is None:
            if not isdir("out"):
                mkdir("out")
            source_directory = "out/" + model_name + "/"

        if epochs is None:
            # TODO: Maybe 50 is a good number? Last one was 60.
            # TODO: change over to optimizing the training set first, then perhaps once the collection for test builds enough, use that.
            # Use the normal loss for the experiments and the first model after that.
            # Use '-sb', '-mm', 'val_loss' after generation(?) to optimize the test set.
            training_output = subprocess.Popen(
                [
                    "precise-train",
                    "-e",
                    "50",
                    "-s",
                    "0.215",
                    "-b",
                    "100",
                    "-sb",
                    "out/" + model_name + ".net",
                    source_directory,
                ],
                stdout=subprocess.PIPE,
            )
        else:
            training_output = subprocess.Popen(
                [
                    "precise-train",
                    "-e",
                    epochs,
                    "-s",
                    "0.215",
                    "-b",
                    "100",
                    "-sb",
                    "out/" + model_name + ".net",
                    source_directory,
                ],
                stdout=subprocess.PIPE,
            )
            # training_output = subprocess.Popen(['precise-train', '-e', epochs, '-b', '100', '-sb', model_name + '.net', source_directory], stdout=subprocess.PIPE)

        stdout = training_output.communicate()
        return stdout[0].decode("utf-8").split("\n")

    def get_last_epoch_model_info(self, model_name, training_run):

        last_epoch = training_run[-2:]
        last_epoch_values = last_epoch[0].split(" - ")
        model_accuracy = {}
        acc = float(last_epoch_values[3].strip("acc: "))
        val_acc = float(last_epoch_values[5].strip("val_acc: "))
        difference = abs(acc - val_acc)
        model_accuracy["acc"] = acc
        model_accuracy["val_acc"] = val_acc
        model_accuracy["difference"] = difference
        self.models[model_name] = model_accuracy

    # TODO: This and all of the other stuff for models will be from model_analytics.py
    def get_model_info(self, model_name, training_run):
        self.model_analytics_instance.add_model(model_name, training_run)
        # return self.models['model_name']

    # TODO: re-factor get_model_analytics to work with the new model_info
    # TODO: then re-factor:
    # get_max_difference
    # remove_model_with_max_difference,
    # get_max_testing_accuracy
    # get_max_train_accuracy

    def run_experimental_training(self, model_names):
        for model_name in model_names:
            # TODO: add optional parameter for sb to precise_train
            training_run = self.run_precise_train(model_name)
            # TODO: This will be replaced with get_model_info
            # self.get_last_epoch_model_info(model_name, training_run)
            self.model_analytics_instance.add_model(model_name, training_run)

    def get_models_analytics(self):
        # average and standard deviation of acc and val_acc
        # TODO: This will be deprecated in favor of model_analytics.py
        # TODO: This will be turned into a get_optimal_test_models_analytics
        acc_list = []
        val_acc_list = []

        for item in self.models.items():
            acc = item[1]["acc"]
            acc_list.append(acc)
            val_acc = item[1]["val_acc"]
            val_acc_list.append(val_acc)
        return (
            statistics.mean(val_acc_list),
            statistics.stdev(val_acc_list),
            statistics.mean(acc_list),
            statistics.stdev(acc_list),
        )

    def get_optimal_training_model_analytics(self):
        """This is a function that shows the average accuracy for training and test values by the best minimum loss of each model"""
        # TODO: cross check parameters with get_models_analytics
        (
            average_acc_for_min_loss_models,
            stdev_acc_for_min_loss_models,
            average_val_acc_for_min_loss_models,
            stdev_val_acc_for_min_loss_models,
            average_acc_for_min_val_loss_models,
            stdev_acc_for_min_val_loss_models,
            average_val_acc_for_min_val_loss_models,
            stdev_val_acc_for_min_val_loss_models,
        ) = self.model_analytics_instance.get_model_analytics()
        return (
            average_acc_for_min_loss_models,
            stdev_acc_for_min_loss_models,
            average_val_acc_for_min_loss_models,
            stdev_val_acc_for_min_loss_models,
        )
        # TODO: Include the average and standard deviation of the training/test set for each!

    def get_optimal_training_model_analytics(self):
        """This is a function that shows the average accuracy for training and test values by the best minimum loss of each model"""
        # TODO: cross check parameters with get_models_analytics
        (
            average_acc_for_min_loss_models,
            stdev_acc_for_min_loss_models,
            average_val_acc_for_min_loss_models,
            stdev_val_acc_for_min_loss_models,
            average_acc_for_min_val_loss_models,
            stdev_acc_for_min_val_loss_models,
            average_val_acc_for_min_val_loss_models,
            stdev_val_acc_for_min_val_loss_models,
        ) = self.model_analytics_instance.get_model_analytics()
        return (
            average_acc_for_min_loss_models,
            stdev_acc_for_min_loss_models,
            average_val_acc_for_min_loss_models,
            stdev_val_acc_for_min_loss_models,
        )
        # TODO: Include the average and standard deviation of the training/test set for each!

    def get_max_difference(self):
        # TODO: follow up, this is diabled for now
        difference_list = []

        for item in self.models.items():
            difference = item[1]["difference"]
            difference_list.append(difference)
        return max(difference_list)

    def remove_model_with_max_difference(self):
        # TODO: follow up, this is diabled for now
        # returns dictionary without max difference model
        best_models = {}
        difference_max = self.get_max_difference()

        for item in self.models.items():
            model_name = item[0]
            difference = item[1]["difference"]
            acc = item[1]["acc"]
            val_acc = item[1]["val_acc"]
            if difference is not difference_max:
                best_model_accuracy = {}
                best_model_accuracy["acc"] = acc
                best_model_accuracy["val_acc"] = val_acc
                best_model_accuracy["difference"] = difference
                best_models[model_name] = best_model_accuracy
        return best_models

    def get_max_testing_accuracy(self, models):
        val_acc_list = []

        for item in models.items():
            val_acc = item[1]["val_acc"]
            val_acc_list.append(val_acc)
        return max(val_acc_list)

    def get_max_training_accuracy(self, models):
        acc_list = []

        for item in models.items():
            acc = item[1]["acc"]
            acc_list.append(acc)
        return max(acc_list)

    def get_best_loss_model(self):
        (
            best_model_loss_name,
            best_val_loss_name,
        ) = self.model_analytics_instance.get_best_model_names()
        return best_model_loss_name, self.models[best_model_loss_name]

    def pick_best_model(self):
        """# pick model with max val_acc (return model)
        best_models = self.remove_model_with_max_difference()
        acc_max = self.get_max_training_accuracy(best_models)
        # val_acc_max = self.get_max_testing_accuracy(best_models)

        for item in best_models.items():
            if item[1]["acc"] is acc_max:
                selected_model = item
                selected_model_name = selected_model[0]

        selected_model_results = selected_model[1]
        return selected_model_name, selected_model_results"""
        best_models = self.model_analytics_instance.get_best_models()
        print(f"best models: {best_models}")
        best_training_set_accuracy_model = best_models[0]
        best_training_set_accuracy_model_name = best_training_set_accuracy_model.keys()
        return best_training_set_accuracy_model

    def delete_experiment_directories(self, selected_model_name):
        # get all directories
        # remove if not best model directory
        basic_file_operations_instance = BasicFileOperations()
        for model in self.models:
            if model is not selected_model_name:
                model_directory = "out/" + model + "/"
                basic_file_operations_instance.delete_directory(model_directory)

    def delete_model(self, model):
        basic_file_operations_instance = BasicFileOperations()
        model_extensions = [".logs", ".net", ".epoch", ".net.params", ".trained.txt"]

        for extension in model_extensions:
            file_to_delete = "out/" + model + extension

            if extension is ".logs":
                basic_file_operations_instance.delete_directory(file_to_delete)
            elif extension is ".net":
                if isdir(file_to_delete):
                    basic_file_operations_instance.delete_directory(file_to_delete)
                else:
                    basic_file_operations_instance.delete_file(file_to_delete)
            else:
                basic_file_operations_instance.delete_file(file_to_delete)

    def delete_generated_directories(self, model_name):
        source_directories = [
            "out/" + model_name + "/not-wake-word/generated/",
            "out/" + model_name + "/test/not-wake-word/generated/",
        ]
        basic_file_operations_instance = BasicFileOperations()
        for directory in source_directories:
            basic_file_operations_instance.delete_directory(directory)

    def delete_experiment_models(self, selected_model_name):
        for model in self.models:
            if model is not selected_model_name:
                self.delete_model(model)

    def rename_model(self, model_name, selected_model_name):
        basic_file_operations_instance = BasicFileOperations()
        model_extensions = [".net", ".epoch", ".net.params", ".trained.txt", ".logs"]

        for extension in model_extensions:
            file_to_rename = "out/" + model_name + extension
            new_file_name = "out/" + selected_model_name + extension
            if extension is ".logs":
                basic_file_operations_instance.rename_directory(
                    file_to_rename + "/", new_file_name + "/"
                )
            else:
                basic_file_operations_instance.rename_file(
                    file_to_rename, new_file_name
                )

    # TODO: write a function to make a temporary copy of the model
    def copy_model(self, model_name):
        basic_file_operations_instance = BasicFileOperations()
        # I removed .training.txt from copying as there is none for this model since it only runs with normal training
        # TODO: Should I save the .trained.txt file from the incremental training?
        model_extensions = [
            ".net",
            ".epoch",
            ".net.params",
        ]

        for extension in model_extensions:
            file_to_copy = "out/" + model_name + extension
            renamed_copy = "out/" + model_name + "_tmp_copy" + extension
            basic_file_operations_instance.backup_file(file_to_copy, renamed_copy)
        return model_name + "_tmp_copy"

    def incremental_training(self, model_name, incremental_data_directory):
        # cool idea: number of files done, number remaining?
        source_directory = "out/" + model_name + "/"
        # copy model to same path as model_name + '_tmp_copy'
        temporary_model_name = self.copy_model(model_name)
        training_output = subprocess.Popen(
            [
                "precise-train-incremental",
                "out/" + temporary_model_name + ".net",
                source_directory,
                "-r",
                incremental_data_directory,
            ],
            stdout=subprocess.PIPE,
        )
        stdout = training_output.communicate()
        return stdout[0].decode("utf-8").split("\n")

    def multi_incremental_training(self, model_name, incremental_data_directories):
        train_test_split_instance = TrainTestSplit()
        epochs = "50"
        for incremental_data_directory in incremental_data_directories:
            print(f"Incremental training on {incremental_data_directory}")
            self.incremental_training(model_name, incremental_data_directory)
            train_test_split_instance.split_incremental_results(model_name)
            self.delete_generated_directories(model_name)
            self.delete_model(model_name)
            print(f"Training fresh model for {model_name}")
            self.run_precise_train(model_name, epochs)

    @staticmethod
    def add_background_noise(model_name, noise_directory):
        # precise-add-noise automatically performs background mixing on sub-directories
        # perhaps I should run multiple instances and only target specific directories?
        basic_file_operations_instance = BasicFileOperations()
        model_directory = "out/" + model_name + "/"
        destination_directory = model_directory + "background_noise/"
        basic_file_operations_instance.make_directory(destination_directory)
        noise_generation_output = subprocess.Popen(
            [
                "precise-add-noise",
                "-if",
                "5",
                model_directory,
                noise_directory,
                destination_directory,
            ],
            stdout=subprocess.PIPE,
        )
        stdout = noise_generation_output.communicate()
        noise_generation_output = stdout[0].decode("utf-8").split("\n")
        return noise_generation_output

    def move_noise_directories(
        self, model_name, source_directories, destination_directories
    ):
        # should this be in the basic file operations?
        basic_file_operations_instance = BasicFileOperations()
        model_directory = "out/" + model_name + "/"
        for source, destination in zip(source_directories, destination_directories):
            source = model_directory + source
            destination = model_directory + destination
            files = basic_file_operations_instance.get_files(source)
            basic_file_operations_instance.copy_directory(files, source, destination)
            # TODO TEST THIS
        basic_file_operations_instance.delete_directory(
            model_directory + "background_noise/"
        )

    def listen(self):
        pass


class GaussianNoiseHandler:
    def add_gaussian_noise(self, file, directory):
        basic_file_operations_instance = BasicFileOperations()
        sample_frequency, wave_data = basic_file_operations_instance.read_wave_file(
            directory + file
        )
        gauss_directory = directory + "gauss/"
        basic_file_operations_instance.make_directory(gauss_directory)
        # TODO: pull noise level out and put into data_prep_user_configuration
        for noise_level in [15, 30, 50, 60]:
            noisy_data = wave_data + noise_level * np.random.randn(len(wave_data))
            noisy_data = noisy_data.astype("int16")
            gauss_file_name = file.replace(".wav", "") + "_" + str(noise_level) + ".wav"
            basic_file_operations_instance.write_wave_file(
                gauss_directory + gauss_file_name, sample_frequency, noisy_data
            )

    def add_gaussian_noise_to_directory(self, model_name, directory):
        basic_file_operations_instance = BasicFileOperations()
        source_directory = "out/" + model_name + "/" + directory
        files = basic_file_operations_instance.get_files(source_directory)
        for file in files:
            self.add_gaussian_noise(file, source_directory)

    def add_gaussian_noise_to_directories(self, model_name, directories_to_gauss):
        for directory in directories_to_gauss:
            self.add_gaussian_noise_to_directory(model_name, directory)
