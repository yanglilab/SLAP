import synapseclient
import synapseutils
USER_NAME = ""  # synapse username
PWD = ""  # synapse password
syn = synapseclient.Synapse()
syn.login(USER_NAME, PWD)

dl_list_file_entities = syn.get_download_list("/media/flik/Seagate Basic/alzheimer_dataset/anmerge")