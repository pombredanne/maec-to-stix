# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import os
import collections
import json

class ConfigParser(object):
    def __init__(self, config_directory=None):
        # The path to the directory where the configuration files can be found
        self.config_directory = config_directory
        # The parsed configuration dictionary
        self.config_dict = {}
        # List of supported Actions
        self.supported_actions = []
        # Dictionary of supported Objects and their properties
        self.supported_objects = {}
        self.parse_config()

    def print_config(self):
        """Print the current set of configuration parameters to stdout.
        
        Note: this method prints detailed information about the parsed Indicator
            extraction configuration, including:
                1. The general Indicator extraction parameters (from config/extractor_config.json)
                2. The supported Actions (derived from all of the parsed JSON configuration files)
                3. The supported Objects and their properties (derived from all of the parsed JSON configuration files)
        """
        # Print the general parameters
        print "\n[Configuration Parameters]"
        for key, value in self.config_dict.items():
            if isinstance(value, bool):
                print str(" {0} : {1}").format(key,value)
            elif isinstance(value, dict):
                print str(" {0}").format(key)
                for embedded_key, embedded_value in value.items():
                    print str("   {0} : {1}").format(embedded_key,embedded_value)
        # Print the supported Actions
        print "\n[Supported Actions]"
        for action_name in sorted(self.supported_actions):
            print str(" {0}").format(action_name)
        # Print the supported Objects
        print "\n[Supported Objects]"
        for object_type in sorted(self.supported_objects):
            supported_fields = self.supported_objects[object_type]
            print str(" {0}").format(object_type)
            required = supported_fields["required"]
            mutually_exclusive_required = supported_fields["mutually_exclusive"]
            optional = supported_fields["optional"]
            if required:
                print "   Required Fields"
                for field in sorted(required):
                    print  str("      {0}").format(field)
            if mutually_exclusive_required:
                print "   Mutually Exclusive (Required) Fields"
                for field in sorted(mutually_exclusive_required):
                    print  str("      {0}").format(field)
            if optional:
                print "   Optional Fields"
                for field in sorted(optional):
                    print  str("      {0}").format(field)

    def _parse_object_config_dict(self, object_type, config_dict):
        """Parse an Object configuration dictionary."""
        flattened_dict = ConfigParser.flatten_dict(config_dict)
        for key, config_options in flattened_dict.items():
            if config_options["enabled"]:
                if object_type not in self.supported_objects:
                    self.supported_objects[object_type] = {"required":{}, "optional":{}, 
                                                           "mutually_exclusive":{}}
                if config_options["required"]:
                    if "mutually_exclusive" in config_options and config_options["mutually_exclusive"]:
                        self.supported_objects[object_type]["mutually_exclusive"][key] = config_options.get("whitelist", None)
                    else:
                        self.supported_objects[object_type]["required"][key] = config_options.get("whitelist", None)
                else:
                    self.supported_objects[object_type]["optional"][key] = config_options.get("whitelist", None)

    def _parse_granular_config(self, granular_config_file):
        """Parse a granular JSON configuration structure."""
        try:
            # Load the default installed configuration file if no directory is specified
            if not self.config_directory:
                config_filename = os.path.join(os.path.dirname(__file__) + "/config", granular_config_file)
            # Otherwise, load the specified configuration file
            else:
                config_filename = os.path.join(self.config_directory, granular_config_file)
            with open(config_filename, mode='r') as f:
                config = json.loads(f.read())
        except EnvironmentError:
            print "Error reading configuration file: " + granular_config_file
            raise
        for config_type, config_values in config.items():
            if config_type == "supported objects":
                for object_type, properties_dict in config_values.items():
                    self._parse_object_config_dict(object_type, properties_dict)
            elif config_type == "supported actions":
                for enum_name, actions_dict in config_values.items():
                    for action_name, enabled in actions_dict.items():
                        if enabled:
                            self.supported_actions.append(action_name)

    def parse_config(self):
        """Parse the JSON configuration structure and build the appropriate data structures."""
        # Parse and load the configuration file
        try:
            # Load the default installed configuration file if no directory is specified
            if not self.config_directory:
                config_filename = os.path.join(os.path.dirname(__file__) + "/config", "extractor_config.json")
            # Otherwise, load the specified configuration file
            else:
                config_filename = os.path.join(self.config_directory, "extractor_config.json")
            with open(config_filename, mode='r') as f:
                self.config_dict = json.loads(f.read())
        except EnvironmentError:
            print "Error reading extractor configuration file."
            raise
        # Use the granular options structure if specified
        if self.config_dict["use_granular_options"]:
            self._parse_granular_config("granular_config.json")
        else:
            abstracted_options = self.config_dict["abstracted_options"]
            for option, enabled in abstracted_options.items():
                if option == "file_system_activity" and enabled:
                    self._parse_granular_config("file_system_activity_config.json")
                elif option == "registry_activity" and enabled:
                    self._parse_granular_config("registry_activity_config.json")
                elif option == "mutex_activity" and enabled:
                    self._parse_granular_config("mutex_activity_config.json")           
                elif option == "process_activity" and enabled:
                    self._parse_granular_config("process_activity_config.json")
                elif option == "service_activity" and enabled:
                    self._parse_granular_config("service_activity_config.json")
                elif option == "network_activity" and enabled:
                    self._parse_granular_config("network_activity_config.json")
                elif option == "driver_activity" and enabled:
                    self._parse_granular_config("driver_activity_config.json")

    @staticmethod
    def flatten_dict(d, parent_key='', sep='/'):
        """Flatten a nested dictionary into one with a single set of key/value pairs.
        
        Args:
            d: an input dictionary to flatten.
            parent_key: the parent_key, for use in building the root key name
                when handling nested dictionaries.
            sep: the separator to use between the concatenated keys in the root key.

        Return:
            The flattened representation of the input dictionary.
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                if "enabled" not in v and "required" not in v:
                    items.extend(ConfigParser.flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            elif isinstance(v, list):
                for list_item in v:
                    items.extend(ConfigParser.flatten_dict(list_item, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)