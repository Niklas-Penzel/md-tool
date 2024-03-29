import tkinter as tk 
import os
from utils import *
from tkinter import messagebox
from tkinter import filedialog
from process_description import PD_handler

def extract_keywords(path, skip_pd=False):
    """
    Function to extract the keywords from a given Metadata file

        path    - string    ... path to the file
    returns:
        keys    - list      ... a list containing the keywords foun in the file
    """
    with open(path, "r") as f:
        lines = f.readlines()
    if not skip_pd:
        # if process description should not be skipped
        if lines[1] == "\n":
            lines = lines[2:]
        else:
            lines = lines[1:]
    else:
        if lines[1] == "\n":
            lines = lines[3:]
        else:
            lines = lines[2:]


    keys = [line.split(":")[0] for line in lines]
    return keys

def extract_process_description(path):
    """
    Function to extract the process description from a given Metadata file

        path    - string    ... path to the file
    returns:
        pd      - string    ... contains the extracted process description
    """
    with open(path, "r") as f:
        lines = f.readlines()

    lines = [line.replace("\n", "") for line in lines]

    if lines[1] == "":
        pd = lines[2].split("::  ")[1]
    else:
        pd = lines[1].split("::  ")[1]

    return pd


def recover_keywords():
    """
    The purpose of this Function is to recover keywords from a given metadata file
    or initialize new empty keywords
    """
    root = tk.Tk()
    root.withdraw()

    if os.path.isfile("keywords.pkl"):
        print("You do not want to go there yet!")
        exit()

    if messagebox.askyesno("Recovering Keywords", "Yes: to try and recover from Metadata from metadata file\nNo:  to create a new empty keyword file"):
        keys = extract_keywords(filedialog.askopenfilename())
        
        if messagebox.askyesno("Found Keys", "Found the following keys:\n"+str(keys)+"\nDo you want to save them?"):
            save_keywords(keys)
            return True
    else:
        if messagebox.askyesno("Recovering Keywords", "Warning: this could overwrite existing Metadata\n\nYes: to initialize new empty keywords.pkl\nNo:  to cancel"):
            save_keywords(["process description"])
            return True
    return False


def recover_processes():
    """
    The purpose of this Function is to recover processes from a given working directory
    or initialize new empty processes
    """
    root = tk.Tk()
    root.withdraw()

    if os.path.isfile("processes.pkl"):
        print("You do not want to go there yet!")
        exit()

    if messagebox.askyesno("Recovering Process Description", "Yes: to try and recover them from a data directory\nNo:  to create an empty processes.pkl"):
        dir = filedialog.askdirectory()
        # initialize metadata file list
        metadata_file_list = []

        # create directory walk
        w = os.walk(dir)
        # filling the list with all file paths
        for root, _, files in w:
            # iterate over all files
            for f in files:
                # create the path
                path = os.path.join(root, f)

                # check if metadata is in the filename or directory above
                if  "metadata" in f or "metadata" in os.path.split(root)[1]:
                    metadata_file_list.append(os.path.normpath(path))

        descriptions = []

        # loop over the metadata files and search non empty descriptions
        for md in metadata_file_list:
            pd = extract_process_description(md)

            if pd != "":
                descriptions.append(pd)

        # create empty process handler
        processes = PD_handler()

        if len(descriptions) == 0:
            if messagebox.askyesno("Recovering Process Descriptions", "Could not find existing descriptions\n\nDo you want to initalize an empty processes.pkl?"):
                save_processes(processes)
                return True
            else:
                return False

        if messagebox.askyesno("Recovering Process Descriptions", "Found the following descriptions:\n" + str(descriptions) + "\nDo you want to save them?"):
            for i,descr in enumerate(descriptions):
                processes["descr_"+str(i+1)] = descr

            save_processes(processes)
            messagebox.showinfo("Attention", "The descriptions where saved with placeholder names!\nTo change the names use the edit description button in the tool.")
            return True       
    else:
        if messagebox.askyesno("Recovering Process Descriptions", "Warning: this could overwrite existing Process Descriptions\n\nYes: to initialize an empty processes.pkl\nNo:  to cancel"):
            save_processes(PD_handler())
            return True
    return False


def recover_from_other_users(path, keywords, processes):
    """
    Function which tries to recover process descriptions and keywords from other 
    users or instances of this tool which use their own keywords.pkl and processes.pkl.

        path        - string        ... path to the working directory
        keywords    - list          ... containing the known keywords
        processes   - PD_handler    ... contains the known processes
    returns
        bools       - tuple         ... should keywords.pkl and processes.pkl be reloaded
    """
    # initialize metadata file list
    metadata_file_list = []

    # create directory walk
    w = os.walk(path)
    # filling the list with all file paths
    for root, _, files in w:
        # iterate over all files
        for f in files:
            # create the path
            path = os.path.join(root, f)

            # check if metadata is in the filename or directory above
            if  "metadata" in f or "metadata" in os.path.split(root)[1]:
                metadata_file_list.append(os.path.normpath(path))

    keys = []
    pds = []
    # iterate over the found md_files and save the found keys/pds
    for md_file in metadata_file_list:
        k = extract_keywords(md_file, skip_pd=False)
        # check process description is differently named:
        if k[0] != keywords[0]:
            # calculate path to the data file
            path = os.path.join(os.path.split(os.path.split(md_file)[0])[0], 
                                "-".join(os.path.split(md_file)[1].replace("-metadata.txt", "").split("-")[:-1])+"."+os.path.split(md_file)[1].replace("-metadata.txt", "").split("-")[-1])
            # create md file and overwrite the name
            tmp = MD_file(path, k)
            tmp.read()
            tmp.update_keyword(0, keywords[0])
            tmp.write()

        k = k[1:]
        dif = list(set(k)-set(keys))
        keys.extend(dif)

        p = extract_process_description(md_file)
        if not p in pds:
            pds.append(p)

    # get the elements not already found in processes.pkl and keywords.pkl
    not_saved_keys = list(set(keys) - set(keywords))
    not_saved_pds = list(set(pds) - set(processes.get_process_descriptions()))

    if len(not_saved_keys) > 0:
        # if keys were found show them to the user and ask if he wants to save them
        if messagebox.askyesno("Found unknown Keywords!", "The following unkown keywords were found in the working directory:\n" + str(not_saved_keys)
            + "\nDo you want to update your keywords.pkl?\n\nWarning: not updating will delete metadata in these unkown keywords."):
            keywords.extend(not_saved_keys)
            save_keywords(keywords)
            # true as in reload keywords
            reload_keywords = True
        else:
            # as in do not reload keywords
            reload_keywords = False
    else:
        reload_keywords = False

    if len(not_saved_pds) > 0:
        if messagebox.askyesno("Found unknown Process Descriptions!", "The following unkown process descriptions were found in the working directory:\n" + str(not_saved_pds)
            + "\nDo you want to update your processes.pkl?\n\nWarning: not updating will delete these process descriptions (metadata could be lost). Saving them will save them with placeholder names."):
            for i,pd in enumerate(not_saved_pds):
                name = "descr_"+str(i)
                p_names = processes.get_process_names()
                j=1
                while name in p_names:
                    name = name.split("(")[0]
                    name = name+"("+str(j)+")"
                    j+=1

                processes[[pd]] = name

            save_processes(processes)

            # return true as in reload processes
            reload_processes = True
        else:
            # as in do not reload processes
            reload_processes = False
    else:
        reload_processes = False

    return reload_keywords, reload_processes
    