import os, json, datetime

from django.shortcuts import render
from django.http import HttpResponse
from django.template import Context, loader, RequestContext, Template
from django.contrib.auth.decorators import login_required

# NOTE: If anyone ever has to update this tool, in hindsight, the structure of it
# feels really confusing, but effectively what it does is uses ajax to communicate between 
# the js portion to give users continuous updates, then this file which manages creating 
# and distroying the directories which tcrdist runs on, then finally the tcr_dist.py file
# which invokes tcrdist (in python2) which operates on the data. My one regret is confusing 
# treatment of when directories are deleted.

def index(request):
    context = {}
    if request.user.is_authenticated:
        context["user_authenticated"]=True
        context["username"]=request.user.username
    return render(request, "tcr_distance/index.html", context)

# creates a random unique directory number and internally creates a directory.
def request_directory(request):
    if request.method == "POST":
        from . import tcr_distance
        dir_num = tcr_distance.create_random_directory()
        tcr_distance.remove_bad_dirs()
        
        response_data = { "dirNum" : dir_num }
        return HttpResponse( json.dumps(response_data), content_type="application/json" )  
    else:
        return HttpResponse( json.dumps({"no" : "not like this"}), content_type="application/json" )  

#
# does the main pipeline code
# destroys the directory after done regardless
def start_tcr_pipeline(request):
    if request.method == 'POST':
        # Process data a bit
        data = request.POST

        # Read the input files in chunks if they exist. Favour clones_file above others.
        clones_file, filtered_contig_annotations, consensus_annotations = b'', b'', b''
        if 'filecf' in request.FILES:
            input_kind = "clones_file"
            if request.FILES['filecf'].size > 500000000:
                return HttpResponse("file too big")

            for chunk in request.FILES['filecf'].chunks():
                clones_file += chunk

            clones_file = clones_file.decode("utf-8")
        elif 'filef' in request.FILES and 'filec' in request.FILES:
            input_kind = "10x"
            if request.FILES['filef'].size > 500000000 or request.FILES['filec'].size > 500000000:
                return HttpResponse("file too big")
                
            for chunk in request.FILES['filef'].chunks():
                filtered_contig_annotations += chunk
            
            for chunk in request.FILES['filec'].chunks():
                consensus_annotations += chunk
          
            filtered_contig_annotations = filtered_contig_annotations.decode("utf-8")
            consensus_annotations = consensus_annotations.decode("utf-8")
        else:
            return HttpResponse("need files")

        if input_kind == "10x" and filtered_contig_annotations == "" or consensus_annotations == "":
            return HttpResponse("file empty")
        elif input_kind == "clones_file" and clones_file == "":
            return HttpResponse("file empty")

        if not "organism" in data:
            return HttpResponse("need organism")
        organism = ("human" if (data["organism"] == "human") else "mouse")

        # check if the directory number is okay
        try:
            dir_num = int(data["dirNum"])
        except ValueError:
            return HttpReponse("bad dirNum")
	
        # Get options
        import re
        send_email = (1 if "sendEmail" in data else 0)
        email_address = data['emailAddress'] if send_email == 1 else ""
        if send_email == 1:
            if email_address == "" or not re.match(r"[^@]+@[^@]+\.[^@]+", email_address):
                return HttpResponse("need email")
	
        download_file = (1 if "download" in data else 0)
        forward_to_visualizer = (1 if "visualizer" in data else 0)

        # Run actual calulation (by passing data)
        import threading
        from . import tcr_distance
        thread = threading.Thread(target=tcr_distance.run, args=(input_kind, filtered_contig_annotations, consensus_annotations, clones_file,
                                     dir_num, organism, send_email, email_address, download_file, forward_to_visualizer))
        thread.daemon = True
        thread.start() # This runs pipeline in the background 

        return HttpResponse("started pipeline")
    else:
        return HttpResponse("use form")

# reads from a special file called 'status'
def get_status(request):
    if request.method == 'GET':
        dirNum = request.GET["dirNum"]
        
        tmp_dirs_path = os.path.dirname(os.path.realpath(__file__)) + "/tmp_dirs"
        status_file_path = "{}/tmp_{}/status".format(tmp_dirs_path, dirNum)
        if not os.path.exists(status_file_path):
            return HttpResponse("requested status doesn't exist")

        with open(status_file_path, "r") as file:
            file_text = file.read()
        
        if file_text.split("\n")[-2] == "request download":
            return HttpResponse("request download") 
        elif file_text.split("\n")[-2] == "no download":
            terminate_directory(dirNum) # writes terminate file
            return HttpResponse("no download")
        
        return HttpResponse(file_text) 
    else:
        return HttpResponse("not allowed")

def download_file(request):
    if request.method == "POST":
        if "dirNum" in request.POST:
            dirNum = request.POST["dirNum"]
        else:
            return HttpResponse("no dir")

        file_path = os.path.dirname(os.path.realpath(__file__)) + "/tmp_dirs/tmp_{}/matricies.zip".format(dirNum)
        if not (os.path.exists(file_path) and os.path.isfile(file_path)):
            return HttpResponse("no file" + str(dirNum))

        with open(file_path, "rb") as file:
            file_dat = file.read()
    
        from . import tcr_distance
        tcr_distance.remove_bad_dirs()
     
        terminate_directory(dirNum) # tell self to be destroyed on the next check -> there should only ever be 1 left over.
 
        response = HttpResponse(file_dat, content_type="application/zip")
        response['Content-Disposition'] = "inline; filename=matricies.zip"
        return response
    else:
        return HttpResponse("not allowed")

# writes 'terminate' to a special file called 'terminate'
def terminate(request):
    if request.method == 'POST':
        from . import tcr_distance
        tcr_distance.remove_bad_dirs()
     
        dir_num = request.POST["dirNum"]
        if terminate_directory(dir_num) == True:
            return HttpResponse("success")
        else:
            return HttpResponse("no dir") 

        return HttpResponse("success") 
    else:
        return HttpResponse("not allowed")

# This function writes the terminate file to a directory.
def terminate_directory(dirNum):
    # wd -> working directory
    wd_path = os.path.dirname(os.path.realpath(__file__)) + "/tmp_dirs/tmp_{}".format(dirNum)
    if not os.path.exists(wd_path):
        return False

    with open(wd_path + "/terminate", "w") as file:
        file.write("terminate")

    return True

