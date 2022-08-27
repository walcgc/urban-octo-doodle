'''
I assume that I am parsing data from Java interface (repository), not class
'''

import argparse
import os
from posixpath import split
import re
import csv
import logging
from time import sleep
from datetime import datetime

dt = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

def main():


    workingdir = os.getcwd()
    fields = ["service", "class", "return type", "method name", "query", "parameters"]
    service = get_proj_folder_name()
    csv_filename = workingdir + "/" + service  + "-" + dt + ".csv"
    initial_write_to_csv(fields, csv_filename)

    for file in scan_files():

        logging.info(file + " - opened")

        with open(file, 'r') as f:
            
            contents = f.read()
            sc_indexes = get_sc_indexes(contents)
            qocs_indexes = get_qocs_indexes(sc_indexes, contents)

            name_of_class = get_ioc_name((file))

            details = find_details(qocs_indexes, contents, service, name_of_class)
            write_to_csv(details, csv_filename)

def get_proj_folder_name():
    cwd = os.getcwd()
    basename = os.path.basename(cwd)
    return basename

def scan_files():
    cwd = os.getcwd()
    list_of_files = []

    for root, dirs, files in os.walk(cwd):
        for file in files:
            fileIsRepository = file.lower().find("repository")
            if fileIsRepository > -1 and file.endswith(".java"):
                list_of_files.append(os.path.join(root, file))

    return list_of_files


# use scan files instead
def list_of_files():

    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    list_of_files = list()

    for arg in args.files:
        list_of_files.append(os.path.abspath(arg))

    return list_of_files

# Get Interface or Class name
def get_ioc_name(filepath):
    index_of_slash = filepath.rfind("/")
    index_of_dot_java = filepath.find(".java")
    return(filepath[index_of_slash+1:index_of_dot_java])

# Get indexes of all semi-colons ; within "public interface" or "public class"
def get_sc_indexes(text):
    # index of interface or class
    index_of_ioc = get_index_of_ioc(text)
    indices = [i.start() for i in re.finditer(";", text)]
    valid_indices = [i for i in indices if i > index_of_ioc]
    return valid_indices

def get_index_of_ioc(text):
    first_ioc = text.find("public interface")
    if first_ioc < -1:
        raise Exception("\"public interface\" or \"public class\" not found")
    
    return first_ioc

# Get query or class start index
# Returns [ [@Query or start location, semi-colon location] ... ]
# [ [qoc, sc], [qoc, sc], [qoc, sc], ... ]
def get_qocs_indexes(sc_indexes, text):
    sc_qocs_pair = list()
    # sp_minus_one = [i - 1 for i in sc_indexes]
    index_of_ioc = get_index_of_ioc(text)
    starting_points = [index_of_ioc] + sc_indexes[:-1]
    sp_count=0

    logging.info("Query or class starting index points - " + str(starting_points))
    
    for sc in sc_indexes:
        # find @Query
        qocs_loc = text.find("@Query", starting_points[sp_count], sc)

        # if @Query not found, find other conditions
        if qocs_loc < 0:
            qocs_loc = text.find(";", starting_points[sp_count], sc)
        if qocs_loc < 0:
            qocs_loc = text.find("{", starting_points[sp_count], sc)
        
        temp_list = [qocs_loc, sc]
        sc_qocs_pair.append(temp_list)
        sp_count += 1

    return sc_qocs_pair


def find_details(index_list, text, service, name_of_class):

    list_of_details = []
    for index in index_list:

        start = index[0]
        end = index[1] + 1

        # for empty repositories
        if start < 0:
            break

        query = ""
        return_type = ""
        method_name = ""
        params = ""

        # Scanning by text section
        text_section = text[start:end]
        # Find @Query
        at_query_exists = text_section.find("@Query") > -1


        if at_query_exists:
            query_end = text_section.find(")\n")+1
            query=text_section[0:query_end]
            

            # Find return type, method name, and params
            method_declaration = text_section[query_end:len(text_section)]
            split_method = method_declaration.split()

            return_type = split_method[0]
            method_name = split_method[1].split("(")[0]
            params_index = method_declaration.find("(")
            params = method_declaration[params_index+1:-2]

        
        else:
            query = "Custom query - DNE"
            split_method = text_section.split()
            return_type = split_method[1]
            method_name = split_method[2].split("(")[0]
            params_index = text_section.find("(")
            params = text_section[params_index+1:-2]

        

        list_of_details.append([service, name_of_class, return_type, method_name, query, params])
    
    return list_of_details
            
        

        
def find_parens(s):
    toret = []
    pstack = []

    for i, c in enumerate(s):
        if c == '(':
            pstack.append(i)
        elif c == ')':
            if len(pstack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            toret.append([pstack.pop(), i])
            
    if len(pstack) > 0:
        raise IndexError("No matching opening parens at: " + str(pstack.pop()))

    return toret

def write_to_csv(details, csv_file):

    f=open(csv_file,'a') 
    write = csv.writer(f, delimiter ='|')

    write.writerows(details)

def initial_write_to_csv(fields, csv_file):
    
    f=open(csv_file,'a') 
    write = csv.writer(f, delimiter ='|')

    write.writerow(fields)

def setup_logger():
    fn = "repo-query-extractor" + dt + ".log"
    logging.basicConfig(filename=fn, format='%(asctime)s - %(message)s', level=logging.INFO)

if __name__ == "__main__":
    setup_logger()
    main()






# ([value])\w+[\S\s]= 
# (?<=value = )([\s\S]*)(?=\))

# (?<=@Query\()(.*\n?)(?=\))
# (?<=@Query\()([\s\S]*)(?=\))     # multiline

# if method contains @Param - scan from there to );

# if no @Query get class by using (
# find class by rfind ; after query

#if re.search(r'(?<=@Query\()([\s\S]*)(?=\))', text_section):
        #print(re.search(r'(?<=@Query\()([\s\S]*)(?=\))', text_section).group(0))
        #print(text_section)


