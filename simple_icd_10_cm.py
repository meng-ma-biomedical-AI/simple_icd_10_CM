import xml.etree.ElementTree as ET

chapter_list = []

code_to_node = {}

all_codes_list = []

all_codes_list_no_dots = []

code_to_index_dictionary = {}

class _CodeTree:
    def __init__(self, tree, parent = None, seven_chr_def_ancestor = None, seven_chr_note_ancestor = None, use_additional_code_ancestor = None, code_first_ancestor = None):
        #initialize all the values
        self.name = ""
        self.description = ""
        self.type = ""
        self.parent = parent
        self.children = []
        self.exclude1 = []
        self.exclude2 = []
        self.includes = []
        self.inclusion_term = []
        self.seven_chr_def = {}
        self.seven_chr_def_ancestor = seven_chr_def_ancestor
        self.seven_chr_note = ""
        self.seven_chr_note_ancestor = seven_chr_note_ancestor
        self.use_additional_code = ""
        self.use_additional_code_ancestor = use_additional_code_ancestor
        self.code_first = ""
        self.code_first_ancestor = code_first_ancestor
        
        #reads the data from the subtrees
        new_seven_chr_def_ancestor=seven_chr_def_ancestor
        new_seven_chr_note_ancestor=seven_chr_note_ancestor
        new_use_additional_code_ancestor=use_additional_code_ancestor
        new_code_first_ancestor=code_first_ancestor
        if "id" in tree.attrib: #the name of sections is an attribute instead of the text in an XML element
            self.name=tree.attrib["id"]
        for subtree in tree:
            if subtree.tag=="section" or subtree.tag=="diag": #creates a new child for this node
                self.children.append(_CodeTree(subtree,parent=self,seven_chr_def_ancestor=new_seven_chr_def_ancestor,seven_chr_note_ancestor=new_seven_chr_note_ancestor,use_additional_code_ancestor=new_use_additional_code_ancestor,code_first_ancestor=new_code_first_ancestor))
            elif subtree.tag=="name":
                self.name=subtree.text
            elif subtree.tag=="desc":
                self.description=subtree.text
            elif subtree.tag=="excludes1":
                for note in subtree:
                    self.exclude1.append(note.text)
            elif subtree.tag=="excludes2":
                for note in subtree:
                    self.exclude2.append(note.text)
            elif subtree.tag=="includes":
                for note in subtree:
                    self.includes.append(note.text)
            elif subtree.tag=="inclusionTerm":
                for note in subtree:
                    self.inclusion_term.append(note.text)
            elif subtree.tag=="sevenChrDef":
                last_char = None
                for extension in subtree:
                    if extension.tag=="extension":
                        self.seven_chr_def[extension.attrib["char"]]=extension.text
                        last_char = extension.attrib["char"]
                    elif extension.tag=="note":
                        self.seven_chr_def[last_char]=self.seven_chr_def[last_char]+"/"+extension.text
                new_seven_chr_def_ancestor=self
            elif subtree.tag=="sevenChrNote":
                self.seven_chr_note=subtree[0].text
                new_seven_chr_note_ancestor=self
            elif subtree.tag=="useAdditionalCode":
                self.use_additional_code=subtree[0].text
                for i in range(1,len(subtree)):#for multiple lines
                    self.use_additional_code=self.use_additional_code+"\n"+subtree[i].text
                new_use_additional_code_ancestor=self
            elif subtree.tag=="codeFirst":
                self.code_first=subtree[0].text
                for i in range(1,len(subtree)):#for multiple lines
                    self.code_first=self.code_first+"\n"+subtree[i].text
                new_code_first_ancestor=self
            
        #sets the type
        if tree.tag=="chapter":
            self.type="chapter"
        elif tree.tag=="section":
            self.type="section"
        elif tree.tag=="diag_ext":
            self.type="extended subcategory"
        elif tree.tag=="diag" and len(self.name)==3:
            self.type="category"
        else:
            self.type="subcategory"
        
        #adds the new node to the dictionary
        if self.name not in code_to_node:#in case a section has the same name of a code (ex B99)
            code_to_node[self.name]=self
        
        #if this code is a leaf, it adds to its children the codes created by adding the seventh character
        if len(self.children)==0 and (self.seven_chr_def!={} or self.seven_chr_def_ancestor!=None) and self.type!="extended subcategory":
            if self.seven_chr_def!={}:
                dictionary = self.seven_chr_def
            else:
                dictionary = self.seven_chr_def_ancestor.seven_chr_def
            extended_name=self.name
            if len(extended_name)==3:
                extended_name=extended_name+"."
            while len(extended_name)<7:#adds the placeholder X if needed
                extended_name = extended_name+"X"
            for extension in dictionary:
                if(extended_name[:3]+extended_name[4:]+extension in all_confirmed_codes):#checks if there's a special rule that excludes this new code
                    new_XML = "<diag_ext><name>"+extended_name+extension+"</name><desc>"+self.description+", "+dictionary[extension]+"</desc></diag_ext>"
                    self.children.append(_CodeTree(ET.fromstring(new_XML),parent=self,seven_chr_def_ancestor=new_seven_chr_def_ancestor,seven_chr_note_ancestor=new_seven_chr_note_ancestor,use_additional_code_ancestor=new_use_additional_code_ancestor,code_first_ancestor=new_code_first_ancestor))

def _load_codes():
    #loads the list of all codes, to remove later from the tree the ones that do not exist for very specific rules not easily extracted from the XML file
    f = open("data/icd10cm-order-Jan-2021.txt", "r")
    global all_confirmed_codes
    all_confirmed_codes = set()
    for line in f:
        all_confirmed_codes.add(line[6:13].strip())
    
    #creates the tree
    tree = ET.parse('data/icd10cm_tabular_2021.xml')
    root = tree.getroot()
    root.remove(root[0])
    root.remove(root[0])
    for child in root:
        chapter_list.append(_CodeTree(child))
    
    del all_confirmed_codes #deletes this list since it won't be needed anymore


_load_codes()

def _add_dot_to_code(code):
    if len(code)<4 or code[3]==".":
        return code
    elif code[:3]+"."+code[3:] in code_to_node:
        return code[:3]+"."+code[3:]
    else:
        return code

def is_valid_item(code):
    return code in code_to_node or len(code)>=4 and code[:3]+"."+code[3:] in code_to_node

def is_chapter(code):
    code = _add_dot_to_code(code)
    if code in code_to_node:
        return code_to_node[code].type=="chapter"
    else:
        return False

def is_block(code):
    code = _add_dot_to_code(code)
    if code in code_to_node:
        return code_to_node[code].type=="section" or code_to_node[code].parent!=None and code_to_node[code].parent.name==code #second half of the or is for sections containing a single category
    else:
        return False

def is_category(code):
    code = _add_dot_to_code(code)
    if code in code_to_node:
        return code_to_node[code].type=="category"
    else:
        return False

def is_subcategory(code, include_extended_subcategories=True):
    code = _add_dot_to_code(code)
    if code in code_to_node:
        return code_to_node[code].type=="subcategory" or code_to_node[code].type=="extended subcategory" and include_extended_subcategories
    else:
        return False

def is_extended_subcategory(code):
    code = _add_dot_to_code(code)
    if code in code_to_node:
        return code_to_node[code].type=="extended subcategory"
    else:
        return False
    
def is_category_or_subcategory(code):
    return is_subcategory(code) or is_category(code)

def is_chapter_or_block(code):
    return is_block(code) or is_chapter(code)

def get_description(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        return node.parent.description
    else:
        return node.description

def get_exclude1(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        return node.parent.exclude1.copy()
    else:
        return node.exclude1.copy()

def get_exclude2(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        return node.parent.exclude2.copy()
    else:
        return node.exclude2.copy()

def get_includes(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        return node.parent.includes.copy()
    else:
        return node.includes.copy()

def get_inclusion_term(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        return node.parent.inclusion_term.copy()
    else:
        return node.inclusion_term.copy()

def get_seven_chr_def(code, search_in_ancestors=False, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    res = node.seven_chr_def.copy()
    if search_in_ancestors and len(res)==0 and node.seven_chr_def_ancestor!=None:
        return node.seven_chr_def_ancestor.seven_chr_def.copy()
    else:
        return res

def get_seven_chr_note(code, search_in_ancestors=False, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    res = node.seven_chr_note
    if search_in_ancestors and res=="" and node.seven_chr_note_ancestor!=None:
        return node.seven_chr_note_ancestor.seven_chr_note
    else:
        return res

def get_use_additional_code(code, search_in_ancestors=False, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    res = node.use_additional_code
    if search_in_ancestors and res=="" and node.use_additional_code_ancestor!=None:
        return node.use_additional_code_ancestor.use_additional_code
    else:
        return res

def get_code_first(code, search_in_ancestors=False, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    res = node.code_first
    if search_in_ancestors and res=="" and node.code_first_ancestor!=None:
        return node.code_first_ancestor.code_first
    else:
        return res

def get_parent(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    if node.parent!=None:
        return node.parent.name
    else:
        return ""

def get_children(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    res = []
    for child in node.children:
        res.append(child.name)
    return res

def is_leaf(code, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    return len(node.children)==0

def get_full_data(code, search_in_ancestors=False, prioritize_blocks=False):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    node = code_to_node[_add_dot_to_code(code)]
    if prioritize_blocks and node.parent!=None and node.parent.name==node.name:
        node = node.parent
    str = "Name:\n"+node.name+"\nDescription:\n"+node.description
    if node.parent!=None:
        str = str + "\nParent:\n" + node.parent.name
    if node.exclude1!=[]:
        str = str + "\nexclude1:"
        for item in node.exclude1:
            str = str + "\n" + item
    if node.exclude2!=[]:
        str = str + "\nexclude2:"
        for item in node.exclude2:
            str = str + "\n" + item
    if node.includes!=[]:
        str = str + "\nincludes:"
        for item in node.includes:
            str = str + "\n" + item
    if node.inclusion_term!=[]:
        str = str + "\ninclusion term:"
        for item in node.inclusion_term:
            str = str + "\n" + item
    seven_chr_note=get_seven_chr_note(code,search_in_ancestors=search_in_ancestors)
    if seven_chr_note!="":
        str = str + "\nseven chr note:\n" + seven_chr_note
    seven_chr_def=get_seven_chr_def(code,search_in_ancestors=search_in_ancestors)
    if seven_chr_def!={}:
        str = str + "\nseven chr def:"
        for item in seven_chr_def:
            str = str + "\n" + item + ":\t" + seven_chr_def[item]
    use_additional=get_use_additional_code(code,search_in_ancestors=search_in_ancestors)
    if use_additional!="":
        str = str + "\nuse additional code:\n" + use_additional
    code_first=get_code_first(code,search_in_ancestors=search_in_ancestors)
    if code_first!="":
        str = str + "\ncode first:\n" + code_first
    if node.children==[]:
        str = str + "\nChildren:\nNone--"
    else:
        str = str + "\nChildren:\n"
        for child in node.children:
            str = str + child.name + ", "
    return str[:-2]
    

'''
def get_descendants(code):
    if not is_valid_item(code):
        raise ValueError(code+" is not a valid ICD-10 code.")
    code = _remove_dot(code)
    if use_memoization:
        if code in descendants_dict:
            return descendants_dict[code].copy()
        else:
            descendants_dict[code] = _get_descendants(code)
            return descendants_dict[code].copy()
    else:
        return _get_descendants(code)

def _get_descendants(code):
    if code in chapter_list:#if it's a chapter
        return _select_adjacent_codes_with_condition(lambda c:_get_chapter(c)==code,_get_index(code))
    elif len(code)==7:#if it's a block
        #we consider first the three blocks whose codes don't all begin with the same letter
        if code=="V01-X59":
            return ["V01-V99", "W00-X59"] + get_descendants("V01-V99") + get_descendants("W00-X59")
        elif code=="W00-X59":
            t = ["W00-W19", "W20-W49", "W50-W64", "W65-W74", "W75-W84", "W85-W99", "X00-X09", "X10-X19", "X20-X29", "X30-X39", "X40-X49", "X50-X57", "X58-X59"]
            return t + [c for l in [get_descendants(x) for x in t] for c in l]
        elif code=="X85-Y09":#this is simpler since all its children are codes
            return _select_adjacent_codes_with_condition(lambda c:not is_chapter_or_block(c) and ((c[0]=="X" and int(code[1:3])>=85) or (c[0]=="Y" and int(code[1:3])<=9)),_get_index(code))
        else:
            #the first part of the lambda expression checks for categories, the second checks for blocks
            return _select_adjacent_codes_with_condition(lambda c:(not is_chapter_or_block(c) and c[0]==code[0] and int(c[1:3])>=int(code[1:3]) and int(c[1:3])<=int(code[-2:]))or(is_chapter_or_block(c) and not c in chapter_list and c[0]==code[0] and int(c[1:3])>=int(code[1:3]) and int(c[-2:])<=int(code[-2:]) and not c==code),_get_index(code))
    elif len(code)==3:#if its a category
        return _select_adjacent_codes_with_condition(lambda c:c[:3]==code and not c==code and len(c)<7,_get_index(code))
    else:#if its a subcategory
        if code=="B180":#two special cases
            return ["B1800", "B1809"]
        elif code=="B181":
            return ["B1810", "B1819"]
        else:
            return []#it has not children

def get_ancestors(code):
    if not is_valid_item(code):
        raise ValueError(code+" is not a valid ICD-10 code.")
    code = _remove_dot(code)
    if use_memoization:
        if code in ancestors_dict:
            return ancestors_dict[code].copy()
        else:
            ancestors_dict[code] = _get_ancestors(code)
            return ancestors_dict[code].copy()
    else:
        return _get_ancestors(code)

def _get_ancestors(code):
    if code in chapter_list:#if its a chapter
        return []#it has no parent
    elif is_chapter_or_block(code):#if its a block
        i = _get_index(code)
        if code=="V01-V99" or code=="W00-X59":#we start with the special cases
            return ["V01-X59"] + get_ancestors("V01-X59")
        elif code=="W00-W19" or code=="W20-W49" or code=="W50-W64" or code=="W65-W74" or code=="W75-W84" or code=="W85-W99" or code=="X00-X09" or code=="X10-X19" or code=="X20-X29" or code=="X30-X39" or code=="X40-X49" or code=="X50-X57" or code=="X58-X59":
            return ["W00-X59"] + get_ancestors("W00-X59")
        else:
            for h in range(1,i+1):
                k=i-h
                if(len(all_codes_no_dots[k])==7 and code[0]==all_codes_no_dots[k][0] and code in get_descendants(all_codes_no_dots[k])):
                    return [all_codes_no_dots[k]] + get_ancestors(all_codes_no_dots[k])
            return [_get_chapter(code)]
    elif len(code)==3:#if its a category
        i = _get_index(code)
        for h in range(1,i+1):
            k=i-h
            if len(all_codes_no_dots[k])==7:#the first category we meet going to the left will contain our code
                return [all_codes_no_dots[k]] + get_ancestors(all_codes_no_dots[k])
    else:#if its a subcategory
        return [code[:-1]] + get_ancestors(code[:-1])

def is_ancestor(a,b):
    if not is_valid_item(a):
        raise ValueError(a+" is not a valid ICD-10 code.")
    return a in get_ancestors(b)

def is_descendant(a,b):
    return is_ancestor(b,a)

def get_nearest_common_ancestor(a,b):
    anc_a = [a] + get_ancestors(a)
    anc_b = [b] + get_ancestors(b)
    if len(anc_b) > len(anc_a):
        temp = anc_a
        anc_a = anc_b
        anc_b = temp
    for anc in anc_a:
        if anc in anc_b:
            return anc
    return ""
    
'''

def get_all_codes(with_dots=True):
    if all_codes_list==[]:
        for chapter in chapter_list:
            _add_tree_to_list(chapter)
    if with_dots:
        return all_codes_list.copy()
    else:
        return all_codes_list_no_dots.copy()

def _add_tree_to_list(tree):
    all_codes_list.append(tree.name)
    if(len(tree.name)>4 and tree.name[3]=="."):
        all_codes_list_no_dots.append(tree.name[:3]+tree.name[4:])
    else:
        all_codes_list_no_dots.append(tree.name)
    for child in tree.children:
        _add_tree_to_list(child)

def get_index(code):
    if not is_valid_item(code):
        raise ValueError("The code \""+code+"\" does not exist.")
    code = _add_dot_to_code(code)
    if all_codes_list==[]:
        for chapter in chapter_list:
            _add_tree_to_list(chapter)
    if code in code_to_index_dictionary:
        return code_to_index_dictionary[code]
    else:
        i=0
        for c in all_codes_list:
            if c==code:
                code_to_index_dictionary[code]=i
                return i
            else:
                i=i+1