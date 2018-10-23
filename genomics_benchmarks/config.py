from configparser import ConfigParser
from shutil import copyfile
import os.path
from pkg_resources import resource_string
from numcodecs import Blosc


def config_str_to_bool(input_str):
    """
    :param input_str: The input string to convert to bool value
    :type input_str: str
    :return: bool
    """
    return input_str.lower() in ['true', '1', 't', 'y', 'yes']


class ConfigurationRepresentation(object):
    """ A small utility class for object representation of a standard config. file. """

    def __init__(self, file_name):
        """ Initializes the configuration representation with a supplied file. """
        parser = ConfigParser()
        parser.optionxform = str  # make option names case sensitive
        found = parser.read(file_name)
        if not found:
            raise ValueError("Configuration file {0} not found".format(file_name))
        for name in parser.sections():
            dict_section = {name: dict(parser.items(name))}  # create dictionary representation for section
            self.__dict__.update(dict_section)  # add section dictionary to root dictionary


class FTPConfigurationRepresentation(object):
    """ Utility class for object representation of FTP module configuration. """
    enabled = False  # Specifies whether the FTP module should be enabled or not
    server = ""  # FTP server to connect to
    username = ""  # Username to login with. Set username and password to blank for anonymous login
    password = ""  # Password to login with. Set username and password to blank for anonymous login
    use_tls = False  # Whether the connection should use TLS encryption
    directory = ""  # Directory on FTP server to download files from
    files = []  # List of files within directory to download. Set to empty list to download all files within directory

    def __init__(self, runtime_config=None):
        """
        Creates an object representation of FTP module configuration data.
        :param runtime_config: runtime_config data to extract FTP settings from
        :type runtime_config: ConfigurationRepresentation
        """
        if runtime_config is not None:
            # Check if [ftp] section exists in config
            if hasattr(runtime_config, "ftp"):
                # Extract relevant settings from config file
                if "enabled" in runtime_config.ftp:
                    self.enabled = config_str_to_bool(runtime_config.ftp["enabled"])
                if "server" in runtime_config.ftp:
                    self.server = runtime_config.ftp["server"]
                if "username" in runtime_config.ftp:
                    self.username = runtime_config.ftp["username"]
                if "password" in runtime_config.ftp:
                    self.password = runtime_config.ftp["password"]
                if "use_tls" in runtime_config.ftp:
                    self.use_tls = config_str_to_bool(runtime_config.ftp["use_tls"])
                if "directory" in runtime_config.ftp:
                    self.directory = runtime_config.ftp["directory"]

                # Convert delimited list of files (string) to Python-style list
                if "file_delimiter" in runtime_config.ftp:
                    delimiter = runtime_config.ftp["file_delimiter"]
                else:
                    delimiter = "|"

                if "files" in runtime_config.ftp:
                    files_str = str(runtime_config.ftp["files"])
                    if files_str == "*":
                        self.files = []
                    else:
                        self.files = files_str.split(delimiter)


vcf_to_zarr_compressor_types = ["Blosc"]
vcf_to_zarr_blosc_algorithm_types = ["zstd", "blosclz", "lz4", "lz4hc", "zlib", "snappy"]
vcf_to_zarr_blosc_shuffle_types = [Blosc.NOSHUFFLE, Blosc.SHUFFLE, Blosc.BITSHUFFLE, Blosc.AUTOSHUFFLE]


class VCFtoZarrConfigurationRepresentation:
    """ Utility class for object representation of VCF to Zarr conversion module configuration. """
    enabled = False  # Specifies whether the VCF to Zarr conversion module should be enabled or not
    compressor = "Blosc"  # Specifies compressor type to use for Zarr conversion
    blosc_compression_algorithm = "zstd"
    blosc_compression_level = 1  # Level of compression to use for Zarr conversion
    blosc_shuffle_mode = Blosc.AUTOSHUFFLE

    def __init__(self, runtime_config=None):
        """
        Creates an object representation of VCF to Zarr Conversion module configuration data.
        :param runtime_config: runtime_config data to extract conversion configuration from
        :type runtime_config: ConfigurationRepresentation
        """
        if runtime_config is not None:
            # Check if [vcf_to_zarr] section exists in config
            if hasattr(runtime_config, "vcf_to_zarr"):
                # Extract relevant settings from config file
                if "enabled" in runtime_config.vcf_to_zarr:
                    self.enabled = config_str_to_bool(runtime_config.vcf_to_zarr["enabled"])
                if "compressor" in runtime_config.vcf_to_zarr:
                    compressor_temp = runtime_config.vcf_to_zarr["compressor"]
                    # Ensure compressor type specified is valid
                    if compressor_temp in vcf_to_zarr_compressor_types:
                        self.compressor = compressor_temp
                if "blosc_compression_algorithm" in runtime_config.vcf_to_zarr:
                    blosc_compression_algorithm_temp = runtime_config.vcf_to_zarr["blosc_compression_algorithm"]
                    if blosc_compression_algorithm_temp in vcf_to_zarr_blosc_algorithm_types:
                        self.blosc_compression_algorithm = blosc_compression_algorithm_temp
                if "blosc_compression_level" in runtime_config.vcf_to_zarr:
                    try:
                        compression_level_temp = int(runtime_config.vcf_to_zarr["blosc_compression_level"])
                        if (compression_level_temp >= 0) and (compression_level_temp <= 9):
                            self.blosc_compression_level = compression_level_temp
                    except ValueError:
                        pass
                if "blosc_shuffle_mode" in runtime_config.vcf_to_zarr:
                    try:
                        blosc_shuffle_mode_temp = int(runtime_config.vcf_to_zarr["blosc_shuffle_mode"])
                        if blosc_shuffle_mode_temp in vcf_to_zarr_blosc_shuffle_types:
                            self.blosc_shuffle_mode = blosc_shuffle_mode_temp
                    except ValueError:
                        pass


def read_configuration(location):
    """
    Args: location of the configuration file, existing configuration dictionary
    Returns: a dictionary of the form
    <dict>.<section>[<option>] and the corresponding values.
    """
    config = ConfigurationRepresentation(location)
    return config


def generate_default_config_file(output_location, overwrite=False):
    # Get Default Config File Data as Package Resource
    default_config_file_data = resource_string(__name__, 'config/benchmark.conf.default')

    if overwrite is None:
        overwrite = False

    if output_location is not None:
        # Check if a file currently exists at the location
        if os.path.exists(output_location) and not overwrite:
            print(
                "[Config] Could not generate configuration file: file exists at specified destination and overwrite mode disabled.")
            return

        # Write the default configuration file to specified location
        with open(output_location, 'wb') as output_file:
            output_file.write(default_config_file_data)

        # Check whether configuration file now exists and report status
        if os.path.exists(output_location):
            print("[Config] Configuration file has been generated successfully.")
        else:
            print("[Config] Configuration file was not generated.")