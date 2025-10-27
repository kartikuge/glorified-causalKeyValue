import socket
import threading
import sys
import time
import random
#using sys import to assign different port numbers to different set of servers and clients
#in the same terminal window

#Terminal prompts:
'''
1. Start the data centers first in different windows: 

python serverAndPeer.py 0 8000 
python serverAndPeer.py 1 8001 
python serverAndPeer.py 2 8002 

2. Start the client operations:

python3 serverAndPeer.py client 8000 'write x lost_ring'
python3 serverAndPeer.py client 8000 'write y found_ring'

python3 serverAndPeer.py client 8001 'write z glad'

and the program should run as required following causal consistency 
'''

version_counter = 0
# a global version counter, global only for the data center


# Data structure to keep track of dependencies
class DependencyTracker:
    def __init__(self):
        self.dependencies = {}

    def update_dependency(self, key, version): #version is the lamport clock
        self.dependencies[key] = version

    def get_dependencies(self):
        return self.dependencies.copy()

    def check_dependencies(self, incoming_dependencies):
        # Check if all dependencies are satisfied
        for key, version in incoming_dependencies.items():
            #checks if the ket exists or lamport clock is up to date
            if key not in self.dependencies or self.dependencies[key] < version:
                return False
        return True

# Function to handle peers at the server
def handle_client(client_socket, data_center_number, dependency_tracker, other_data_centers):
    # Initialize a Lamport clock counter for this data center
    global version_counter

    while True:
        
        #receives message from clients
        data = client_socket.recv(1024).decode()
        
        if not data:
            break
        

        arguments = data.split()
        
        #if there are 3 arguments, its a local client command
        if len(arguments) == 3:
 
            command, key, value = data.split()
            if command == "read":
                
                #clock stays the same for read operation 
                version = (version_counter, data_center_number)

                dependency_tracker.update_dependency(key, version) #nothing will be updated in the list

                response = f"Read {key} with version {version} and message {value}"
                
                #sends message back to client
                client_socket.send(response.encode())

            elif command == "write":
                
                #updates lamport clock by 1 
                version_counter += 1
                version = (version_counter, data_center_number)

                dependencies = dependency_tracker.get_dependencies()
                response = f"Write {key} with message {value} and dependencies {dependencies}"
                client_socket.send(response.encode()) #sends message back to local client

                #starts replicate write for other data centers
                replicate_write(key, version, dependencies, other_data_centers, data_center_number)

                #the dependency list is then updated with the latest write command
                dependency_tracker.update_dependency(key, version)

        #if its not 3 arguments then its a replicate write command
        else:
            
            #since replicate write seperates its arguments with '-' symbol
            command, key, version_str, dependencies_str = data.split('-')

            #handles replicate write for the local data center
            handle_replication(data_center_number, client_socket, dependency_tracker, key, version_str, dependencies_str)

            #when successful it lets the user know 
            print(f"Data Center {data_center_number} processed: {data}")


    #client_socket.close()

def replicate_write(key, version, dependencies, other_data_centers, data_center_number):
    
    #other_data_centers has list of all other port numbers 
    for address in other_data_centers:
        
        #replication write which will be delayed with time.sleep
        def delayed_replication(addressing):

            #simulate network delay between data centers
            if data_center_number == 0 and addressing[1] == 8001:

                time.sleep(2) 
            
            elif data_center_number == 0 and addressing[1] == 8002:
                
                time.sleep(20)

            elif data_center_number == 1 and addressing[1] == 8002:

                time.sleep(1)
        
            #connects this data center to other data centers
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect(addressing)
                #packages replicate message with dependency list and sends it to other data centers
                message = f"replicate-{key}-{version}-{dependencies}"
                client.send(message.encode()) #sends this to other data centers
          
        #creates a new thread for this replicate write for parallel processing 
        threading.Thread(target=delayed_replication, args=(address,)).start()
    

# Function to handle incoming replicated writes
def handle_replication(data_center_number, client_socket, dependency_tracker, key, version_str, dependencies_str):

    #data = client_socket.recv(1024).decode()
    
    global version_counter

    version = eval(version_str)  #converts string to tuple
    dependencies = eval(dependencies_str)  #converts string to dict

    #checks dependencies before committing
    while not dependency_tracker.check_dependencies(dependencies):
        print(f"Data Center {data_center_number}: Write {key} delayed due to unsatisfied dependencies")
        time.sleep(5)  #sleeps and then tries again, in case other threads have not finished processing
    #ideal implementation would mean it stores it in a buffer

    #once dependencies are satisfied, it commits the write
    version_counter += 1 #local lamport clock is also updated accordingly 
    dependency_tracker.update_dependency(key, version)
    print(f"Data Center {data_center_number}: Write {key} committed after replication")

    #client_socket.close()

#function to start a data center
def start_data_center(data_center_number, port, other_data_centers):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', port))
    server.listen(5)
    print(f"Data Center {data_center_number} is running on port {port}")

    dependency_tracker = DependencyTracker()
    
    while True:

        client_socket, addr = server.accept()
        #if there is a client connecting (local peer or other data center) it creates a new thread
        threading.Thread(target=handle_client, args=(client_socket, data_center_number, dependency_tracker, other_data_centers)).start()
    
    '''
    while True:
        client_socket, addr = server.accept()
        initial_message = client_socket.recv(1024).decode()

        if initial_message == "REPLICATION":
            threading.Thread(target=handle_replication, args=(data_center_number, client_socket, dependency_tracker)).start()
        else:
            threading.Thread(target=handle_client, args=(client_socket, data_center_number, dependency_tracker, other_data_centers)).start()

        #client_socket.close()
    '''
#function for local client behavior
def client_behavior(data_center_port, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', data_center_port))
    client.send(message.encode())
    
    response = client.recv(1024).decode()
    print(f"Client received: {response}")
    #client.close()

#main uses inputs from terminal to determine actions
if __name__ == "__main__":
    if sys.argv[1] == "client": #if the user specifies client then it acts as a client
        port = int(sys.argv[2])
        message = sys.argv[3]
        client_behavior(port, message)
    else:
        data_center_number = int(sys.argv[1])
        port = int(sys.argv[2]) 
        
        print(data_center_number)
        print(port)

        #list of data centers in this project
        other_data_centers = [("localhost", 8000), ("localhost", 8001), ("localhost", 8002)]
        other_data_centers.remove(("localhost", port)) #the current data center removes itself from this list 

        #print(other_data_centers)

        start_data_center(data_center_number, port, other_data_centers)

