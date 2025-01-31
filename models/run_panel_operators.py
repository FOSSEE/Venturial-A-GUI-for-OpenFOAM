from bpy.types import Operator
import bpy, itertools, json

# Function to convert a list to string for blockmeshdict file
def listToOFStr(li):
    sr="( "
    for i in li:
        sr=sr+str(i)+" "
    sr=sr+")"
    return(sr)

def write_dict(m, out_fp):
    # Param:
    #     -json_str: it is the json string that have all the data,String type
    #     -out_fp: This is the full file path including its name(generally it is "blockMeshDict),String type"
    # Returns data in python dictionary format

    data=json.loads(m)
    blockdict=[]
        
    #------header start----------
    blockdict.append(r"/*--------------------------------*- C++ -*----------------------------------*\\")
    blockdict.append(r"| =========                 |                                                 |")
    blockdict.append(r"| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |")
    blockdict.append(r"|  \\    /   O peration     | Version:  9                                     |")
    blockdict.append(r"|   \\  /    A nd           | Web:      www.OpenFOAM.org                      |")
    blockdict.append(r"|    \\/     M anipulation  |                                                 |")
    blockdict.append(r"\*---------------------------------------------------------------------------*/")
    blockdict.append(r"//*******This file is generated by Venturial*********//")
    #-------header end-------


    #------details start------
    blockdict.append("FoamFile")
    blockdict.append("{")
    blockdict.append("version     2.0;")
    blockdict.append("format      ascii;")
    blockdict.append("class       dictionary;")
    blockdict.append("object      blockMeshDict;")
    blockdict.append("}")
    #-------details end--------


    #-----convert to m start---------
    #todo
    blockdict.append("convertToMeters "+str(data['convertToMeters'][0])+" ;")
    #------convert to m end------


    #----index start-----
    blockdict.append("vertices")
    blockdict.append("(")
    verts=data['vertices']
    for v in verts:
        blockdict.append(listToOFStr(v))
    blockdict.append(");")
    #----index done-----6


    #-----blocks start-----
    blockdict.append("blocks")
    blockdict.append("(")
    blocks=data['blocks']
    for b in blocks:
        blockdict.append("hex "+listToOFStr(b[0])+" "+listToOFStr(b[1])+" "+b[2])
    blockdict.append(");")
    #------blocks done------
    
    #------edges start---------
    blockdict.append("edges")
    blockdict.append("(")
    edges=data['edges']
    le=len(edges)
    if(le!=0):
        for edg in edges:
            ename=edg[0]+" "+str(edg[1][0])+" "+str(edg[1][1])
            ed=[]
            if(ename[:3]=="arc"):
                blockdict.append(ename+" "+listToOFStr(edg[2][0]))
            else:
                for e in edg[2]:
                    ed.append(listToOFStr(e))

                blockdict.append(ename)
                blockdict.append("(")
                for e in ed:
                    blockdict.append(e)
                blockdict.append(")")
                    
    blockdict.append(");")
    #------edges end------


    #------boundaries start-----
    blockdict.append("boundary")
    blockdict.append("(")
    boundaries=data['boundary']
    li=len(blockdict)
    lb=len(boundaries)
    if(lb!=0):
        while(len(boundaries)!=0):
            bname=boundaries[0][0]
            btype=boundaries[0][1]
            bface=[]
            for b in boundaries:
                if(b[0]==bname):
                    bface.append(listToOFStr(b[2]))
            boundaries=[b for b in boundaries if b[0]!=bname]
            blockdict.append(bname)
            blockdict.append("{")
            blockdict.append("type "+btype+";")
            blockdict.append("faces")
            blockdict.append("(")
            for f in bface:
                blockdict.append(f)
            blockdict.append(");")
            blockdict.append("}")
    blockdict.append(");")
    #--------boundaries end------------

    #-------mergePatchPairs start---------
    #todo
    blockdict.append("mergePatchPairs")
    blockdict.append("(")
    mergePatchPairs=data['mergePatchPairs']
    for mpp in mergePatchPairs:
        blockdict.append(f"({mpp[0]} {mpp[1]})")
    blockdict.append(");")
    #-------mergePatchPairs end---------

    blockdict.append(r"// ************************************************************************* //")

    #print(blockdict)
    fobj = open(out_fp, "w")
    indent=0
    for line in blockdict:
            if(line==")" or line=="}" or line==");"):
                indent-=1
            #print(line)
            sln=(indent*"\t")+line+"\n"
            fobj.write(sln)
            if(line=="(" or line=="{"):
                indent+=1
    fobj.close()
    return(data)



# Converts a vertex coordinate point from string to list of float, 
# example: print(vert_strtolist("(1.64, 3.61, -5.47)")) = [1.64, 3.61, -5.47]
def vert_strtolist(string):
    #Add error handling to avoid errors during parsing
    return [float(i) for i in string[1:-1].split(", ")]                 


# Converts a block represented by hex from string to list of integers,
# example: print(hex_strtolist("hex (0 9 8 7 3 4 5 1)")) = [0, 9, 8, 7, 3, 4, 5, 1]
def hex_strtolist(string):
    #Add error handling to avoid errors during parsing
    return [int(s) for s in string[5: -1].split() if s.isdigit()] 


# Converts a face from string to list of integers,
# example: print(face_strtolist("(9 0 8 7)")) = [9, 0, 8, 7]
def face_strtolist(string):
    #Add error handling to avoid errors during parsing
    return [int(s) for s in string[1: -1].split() if s.isdigit()]


# Converts an edge from string to list of integers,
# example: print(edge_strtolist("polyLine 9 8")) = [9, 8]
def edge_strtolist(string):
    #Add error handling to avoid errors during parsing
    return [int(s) for s in string.split() if s.isdigit()]





class VNT_OT_fill_dict_file(Operator):
    bl_label = "Add all current lists to dictionary File."
    bl_description = "Add all current data from lists to dictionary file.\nClick this button again to add changes made in the list"
    bl_idname = "fill.dictfile"
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        
        bmdict={'convertToMeters':[],
                'vertices':[],
                'blocks':[],  #hex, set cells, simplegrading
                'edges':[], #arc, polyLine, spline, BSpline
                'boundary':[],
                'mergePatchPairs':[]}
        
        scn = context.scene
        
        text_obj = bpy.data.texts[scn.mfile_item[scn.mfile_item_index].ITEM_name + '.json']
        text_str = text_obj.as_string()
        
        bmdict['convertToMeters'].append(scn.ctm)
        
        #Add vertices to Dictionary
        for i in scn.vcustom:
            bmdict['vertices'].append(vert_strtolist(i.name))
            
        #Add blocks to Dictionary
        for i in scn.bcustom:
            bmdict['blocks'].append([hex_strtolist(i.name), [i.setcellx, i.setcelly, i.setcellz], i.grading]) 
            
        #Add boundary(faces) to Dictionary
        for i in scn.fcustom:
            bmdict['boundary'].append([i.face_des, i.face_type, face_strtolist(i.name)])
    
        # Add Edges(arc, polyLine, spline, BSpline) to Dictionary

        # cp_edge_list = [scn.acustom, scn.pcustom, scn.scustom, scn.bscustom]
        # cp_edge_list = [scn.ecustom]
        # edge_type = ["arc", "polyLine", "spline", "BSpline"]     

        for ix in range(0, len(scn.ecustom)): # change the way edges are stored

            ''' Old code
            if ix == 0:
                for i in cp_edge_list[ix]:
                    bmdict['edges'].append([edge_type[ix], edge_strtolist(i.fandl), [i.intptx, i.intpty, i.intptz]])
        
            else:
                tel = [edge_strtolist(i.fandl) for i in cp_edge_list[ix]]        
                tel.sort()
                ret = list(tel for tel,_ in itertools.groupby(tel))
                
                ev = []
                for i in ret:
                    el= []
                    for j in cp_edge_list[ix]:
                        if i == edge_strtolist(j.fandl):
                            el.append([j.intptx, j.intpty, j.intptz])
                    ev.append(el)
            
                for k in range(0, len(ret)):
                    bmdict['edges'].append([edge_type[ix], ret[k], ev[k]])
            
            '''
            
            vert_index = []
            edge = scn.ecustom[ix]

            edge_type = {
                "ARC": "arc",
                "PLY": "polyLine",
                "SPL": "spline",
                "BSPL": "BSpline"
            }

            e_type = edge_type[edge.edge_type]

            vert_index.append(bmdict["vertices"].index(list(edge.vc[0].vert_loc)))
            vert_index.append(bmdict["vertices"].index(list(edge.vc[2].vert_loc)))

            e_verts = []
            length = len(edge.vert_collection)
            for i in range(length):
                _a_ = bpy.data.objects[f"{edge.name}0{i+1}"]
                e_verts.append(list(_a_.location))
            # e_verts = [list(v.vert_loc) for v in edge.vert_collection]
            bmdict["edges"].append([e_type, vert_index, e_verts])  
            
        # Add MergePatchPairs to Dictionary
        for i in scn.fmcustom:
            pair = (i.master_face, i.slave_face)
            bmdict['mergePatchPairs'].append(pair)

        m = json.dumps(bmdict, sort_keys=True, indent=2)
        text_obj.from_string(m) 
        
        
        dire = scn.mfile_item[scn.mfile_item_index].ITEM_location
        
        filnm = scn.mfile_item[scn.mfile_item_index].ITEM_name
        
        write_dict(m, dire + "/" + filnm)
        
        self.report({'INFO'}, "Blockmesh Generated")

        return{'FINISHED'}

# Clear Dictionary File
class VNT_OT_cleardictfileonly(Operator):
    bl_label = "Clear dictionary File. This action cannot be undone."
    bl_description = "Clear all present data from dict file but not from lists.\nClick Add Lists to Dictionary again to add latest data from lists"
    bl_idname = "clear.dictfileonly"
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        
        bmdict={'convertToMeters':[],
                'vertices':[],
                'blocks':[],
                'edges':[],
                'boundary':[],
                'mergePatchPairs':[]}
                
        scn = context.scene
        bmdict['convertToMeters'].append(0)
        
        try:
            
            text_obj = bpy.data.texts[scn.mfile_item[scn.mfile_item_index].ITEM_name + '.json']
            
            text_str = text_obj.as_string()
            m = json.dumps(bmdict, sort_keys=True, indent=2)
            
            text_obj.from_string(m) 
            
            dire = scn.mfile_item[scn.mfile_item_index].ITEM_location
            filnm = scn.mfile_item[scn.mfile_item_index].ITEM_name
            
            write_dict(m, dire + "/" + filnm)
            self.report({'INFO'}, "Dictionary Cleared.")
            
        except KeyError:
            self.report({'INFO'}, "Initialize Dictionary")

        return{'FINISHED'}