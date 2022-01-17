import statistics

"""# Open the json file and load the content
with open('training_run.json', 'r') as file:
    training_run_json = json.load(file)"""


class ModelAnalytics:
    def __init__(self):
        self.models = {}

    # string matches for the lines we want to scrape
    @staticmethod
    def scrape_epoch_training_results(training_run_json):
        training_complete_string = "[==============================]"
        epoch_number = "Epoch"
        # TODO: add in the category counts and return them

        epochs = [line for line in training_run_json if epoch_number in line]

        epoch_training_results = [
            line.split(" - ")[2:]
            for line in training_run_json
            if training_complete_string in line
        ]
        return zip(epoch_training_results, epochs)

    @staticmethod
    def scrape_category_counts(training_run_json):
        category_counts_string = "Data:"
        for line in training_run_json:
            if category_counts_string in line:
                category_counts = line.split(" ")
                return category_counts

    def transform_category_counts(self, training_run_json):
        category_counts = self.scrape_category_counts(training_run_json)
        wake_words_count = int(category_counts[2].strip("wake_words="))
        not_wake_words_count = int(category_counts[3].strip("not_wake_words="))
        test_wake_words_count = int(category_counts[4].strip("test_wake_words="))
        test_not_wake_words_count = int(
            category_counts[5].strip("test_not_wake_words=").strip(">")
        )
        category_counts_dict = {
            "training_data": {
                "wake_words": wake_words_count,
                "not_wake_words": not_wake_words_count,
                "test_wake_words": test_wake_words_count,
                "test_not_wake_words": test_not_wake_words_count,
            }
        }
        return category_counts_dict

    def transform_epoch_number_and_accuracy(self, training_run_json):
        epochs_accuracy = {}
        epochs_training_results = self.scrape_epoch_training_results(training_run_json)
        for epoch_result, epoch_number in epochs_training_results:
            epoch_number = int(epoch_number.strip("Epoch ").rsplit("/", 1)[0])
            loss = float(epoch_result[0].strip("loss: "))
            acc = float(epoch_result[1].strip("acc: "))
            val_loss = float(epoch_result[2].strip("val_loss: "))
            val_acc = float(epoch_result[3].strip("val_acc: "))

            accuracy_dict = {
                "epoch": epoch_number,
                "loss": loss,
                "acc": acc,
                "val_loss": val_loss,
                "val_acc": val_acc,
                "acc_difference": abs(acc - val_acc),
            }

            epochs_accuracy[epoch_number] = accuracy_dict
        return epochs_accuracy

    def get_maximum_accuracy(self, training_run_json):
        epochs_accuracy = self.transform_epoch_number_and_accuracy(training_run_json)
        minimum_loss_accuracy = min(epochs_accuracy.values(), key=lambda x: x["loss"])
        minimum_loss_val_accuracy = min(
            epochs_accuracy.values(), key=lambda x: x["val_loss"]
        )

        return (minimum_loss_accuracy, minimum_loss_val_accuracy)

    def add_model(self, model_name, training_run_json):
        category_counts_dict = self.transform_category_counts(training_run_json)
        minimum_loss_accuracy, minimum_loss_val_accuracy = self.get_maximum_accuracy(
            training_run_json
        )

        self.models[model_name] = [
            {"minimum_loss_accuracy": minimum_loss_accuracy},
            {"minimum_loss_val_accuracy": minimum_loss_val_accuracy},
            category_counts_dict,
        ]
        return self.models

    # This is the part that calculates the smallest minimum_loss and minimum_loss_val_acc for all the models
    # This will have to be changed to get the self.models from PreciseModelingOperations
    def get_model_accuracies(self):
        acc_for_min_loss_models = [
            item[1][0]["minimum_loss_accuracy"]["acc"] for item in self.models.items()
        ]
        val_acc_for_min_loss_models = [
            item[1][0]["minimum_loss_accuracy"]["val_acc"]
            for item in self.models.items()
        ]
        # TODO: add val_acc_for_min_loss_models, acc_for_min_val_loss_models
        acc_for_min_val_loss_models = [
            item[1][1]["minimum_loss_val_accuracy"]["acc"]
            for item in self.models.items()
        ]
        val_acc_for_min_val_loss_models = [
            item[1][1]["minimum_loss_val_accuracy"]["val_acc"]
            for item in self.models.items()
        ]

        return (
            acc_for_min_loss_models,
            val_acc_for_min_loss_models,
            acc_for_min_val_loss_models,
            val_acc_for_min_val_loss_models,
        )

    def get_max_accuracies_over_all_models(self):
        (
            acc_for_min_loss_models,
            val_acc_for_min_loss_models,
            acc_for_min_val_loss_models,
            val_acc_for_min_val_loss_models,
        ) = self.get_model_accuracies()
        max_acc_for_min_loss_model = max(acc_for_min_loss_models)

        max_val_acc_for_min_val_loss_model = max(val_acc_for_min_val_loss_models)

        return (max_acc_for_min_loss_model, max_val_acc_for_min_val_loss_model)

    def get_model_analytics(self):
        """returns the average accuracy for all of the models, it returns the analytics for both the epoch with the lowest loss and the epoch with the lowest val_loss"""
        (
            acc_for_min_loss_models,
            val_acc_for_min_loss_models,
            val_acc_for_min_val_loss_models,
            acc_for_min_val_loss_models,
        ) = self.get_model_accuracies()
        average_acc_for_min_loss_models = statistics.mean(acc_for_min_loss_models)
        stdev_acc_for_min_loss_models = statistics.stdev(acc_for_min_loss_models)
        average_val_acc_for_min_loss_models = statistics.mean(
            val_acc_for_min_loss_models
        )
        stdev_val_acc_for_min_loss_models = statistics.stdev(
            val_acc_for_min_loss_models
        )
        average_acc_for_min_val_loss_models = statistics.mean(
            acc_for_min_val_loss_models
        )
        stdev_acc_for_min_val_loss_models = statistics.stdev(
            acc_for_min_val_loss_models
        )
        average_val_acc_for_min_val_loss_models = statistics.mean(
            val_acc_for_min_val_loss_models
        )
        stdev_val_acc_for_min_val_loss_models = statistics.stdev(
            val_acc_for_min_val_loss_models
        )

        return (
            average_acc_for_min_loss_models,
            stdev_acc_for_min_loss_models,
            average_val_acc_for_min_loss_models,
            stdev_val_acc_for_min_loss_models,
            average_acc_for_min_val_loss_models,
            stdev_acc_for_min_val_loss_models,
            average_val_acc_for_min_val_loss_models,
            stdev_val_acc_for_min_val_loss_models,
        )

    def get_best_model_names(self):
        (
            max_acc_for_min_loss_model,
            max_val_acc_for_min_val_loss_model,
        ) = self.get_max_accuracies_over_all_models()
        best_models = []
        max_acc_for_min_loss_model_dict = {}
        max_val_acc_for_min_val_loss_model_dict = {}
        for item in self.models.items():
            if item[1][0]["minimum_loss_accuracy"]["acc"] == max_acc_for_min_loss_model:
                max_acc_for_min_loss_model_dict[item[0]] = item[1][0]
                best_models.append(max_acc_for_min_loss_model_dict)
            if (
                item[1][1]["minimum_loss_val_accuracy"]["val_acc"]
                == max_val_acc_for_min_val_loss_model
            ):
                max_val_acc_for_min_val_loss_model_dict[item[0]] = item[1][1]
                best_models.append(max_val_acc_for_min_val_loss_model_dict)
        best_model_loss = best_models[0]
        best_model_val_loss = best_models[1]
        best_model_loss_name = list(best_model_loss.keys())[0]
        best_model_val_loss_name = list(best_model_val_loss.keys())[0]
        return (best_model_loss_name, best_model_val_loss_name)

    # This is used when the training is run for -sb with the loss being the measure (default)
    @staticmethod
    def get_best_max_acc_for_min_loss_model(best_models):
        max_acc_for_min_loss_model_dict = best_models[0]
        return max_acc_for_min_loss_model_dict

    # This is used when the training is run for -sb with the val_loss being the measure (important to optimize when the test set is big enough)
    @staticmethod
    def get_best_max_val_acc_for_min_val_loss_model(best_models):
        max_val_acc_for_min_val_loss_model_dict = best_models[1]
        return max_val_acc_for_min_val_loss_model_dict
