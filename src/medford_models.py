from pydantic import BaseModel, AnyUrl, validator, root_validator
from typing import List, Optional, Union, Iterable
import datetime
from enum import Enum
from helpers_file import *

# bcodmo? + bag
# export to rtf?
# error on unknown fields
# data1 compliance ('dublin core'?)

# Validation of user-defined fields: in the future?
#       runtime clas creation?
#       parser level validation?

# Test against all data types;
#       Return which ones *can* submit to & which *cannot*
#       Can then re-run on specific mode to see specific errors

################################
# Helper Models                #
################################
class StrDescModel(BaseModel):
    desc: List[str] #TODO: Find a way to make an exception?
    Note: Optional[List[str]]

################################
# Field Models                 #
################################

class Journal(StrDescModel):
    Volume: List[int]
    Issue: List[int]
    Pages: Optional[List[str]] #TODO: Validation?

class Date(BaseModel):
    desc: Union[List[datetime.date], List[datetime.datetime]]
    Note: List[str]
    #changed type to note because type is a reserved keyword

class Contributor(StrDescModel) :
    ORCID: Optional[List[int]]
    Assocation: Optional[List[str]]
    Role: Optional[List[str]]
    Email: Optional[List[str]] #TODO: Email validation

class Funding(StrDescModel) :
    ID: Optional[List[str]] #TODO: Funding ID validation?

class Keyword(StrDescModel):
    pass

class Species(StrDescModel):
    Loc: List[str]
    ReefCollection: List[str] # TODO: Change to date with note?
    Cultured: List[str]
    CultureCollection: List[str]

class Method(StrDescModel):
    Type: List[str]
    Company: Optional[List[str]]
    Sample: Optional[List[str]]

class Project(StrDescModel):
    pass

class Expedition(StrDescModel):
    ShipName: Optional[List[str]]
    CruiseID: Optional[List[str]]
    MooringID: Optional[List[str]]
    DiveNumber: Optional[List[int]]
    Synonyms: Optional[List[str]]

class ArbitraryFile(StrDescModel):
    Path: List[str]
    Subdirectory: Optional[List[str]]
    bagName: Optional[str]

class Freeform(BaseModel):
    class Config:
        extra = 'allow'
    pass

## Multi-Typed tags (data, code, paper)
class LocalBase(StrDescModel):
    Path: Optional[List[str]]
    Subdirectory: Optional[List[str]]
    bagName: Optional[str]

class D_Ref(LocalBase) :
    Type: Optional[List[str]]
    URI: Optional[List[AnyUrl]]

class D_Copy(LocalBase) :
    Type: Optional[List[str]]

class D_Primary(LocalBase) :
    Type: Optional[List[str]]

class Data(BaseModel) :
    Ref: Optional[List[D_Ref]]
    Copy: Optional[List[D_Copy]]
    Primary: Optional[List[D_Primary]]

class P_Ref(LocalBase) :
    Link: Optional[List[AnyUrl]]
    PMID: Optional[List[int]]
    #Add a validator for PMID?
    DOI: Optional[List[datetime.date]]

class P_Copy(StrDescModel) :
    Link: Optional[List[AnyUrl]]
    PMID: Optional[List[int]]
    #Add a validator for PMID?
    DOI: Optional[List[datetime.date]]

class P_Primary(StrDescModel) :
    Link: Optional[List[AnyUrl]]
    PMID: Optional[List[int]]
    #Add a validator for PMID?
    DOI: Optional[List[datetime.date]]

class Paper(BaseModel) :
    Ref: Optional[List[P_Ref]]
    Copy: Optional[List[P_Copy]]
    Primary: Optional[List[P_Primary]]

class S_Ref(StrDescModel):
    Type: List[str]
    Version: Optional[List[str]]
    
class S_Copy(LocalBase):
    Type: List[str]
    Version: Optional[List[str]]

class S_Primary(LocalBase):
    Type: List[str]
    Version: Optional[List[str]]

class Software(BaseModel): 
    Ref: Optional[List[S_Ref]]
    Copy: Optional[List[S_Copy]]
    Primary: Optional[List[S_Primary]]
################################
# Overarching Model            #
################################
# Meant to store every single possible tag that we have defined
class Entity(BaseModel):
    Paper: Optional[List[Paper]]
    Journal: Optional[List[Journal]]
    Date: Optional[List[Date]]
    Contributor: Optional[List[Contributor]]

    @validator('Contributor')
    @classmethod
    def ensure_corresponding_have_email(cls, v) :
        for contributor in v:
            roles = [str.lower(x).strip() for x in contributor.Role]
            if 'corresponding author' in roles and contributor.Email is None:
                raise ValueError("ERROR: Contributor " + contributor.desc[0] + " is marked as a corresponding author, but has no provided email.")
                
    Funding: Optional[List[Funding]]
    Keyword: Optional[List[Keyword]]
    Species: Optional[List[Species]]
    Method: Optional[List[Method]]
    Software: Optional[List[Software]]
    Data: Optional[List[Data]]
    File: Optional[List[ArbitraryFile]]
    Freeform: Optional[List[Freeform]]

class BagIt(Entity) :
    Data: List[Data]
    # A BagIt requires:
    #   - at least one recorded Data
    #       (otherwise, what is the point of the bag?)
    #   - arbitrary file definitions?
    #   - The input MEDFORD file
    #
    # For every file (recorded data or arbitrary file definition), MEDFORD
    #   parser has to:
    #   - create a sha-512 hash or sha-256 hash
    #   - copy into an appropriate subdirectory
    #       (default: data/
    #           alternative can be defined using the Subdirectory attribute)
    #   - write down name & final location into a manifest file:
    #       manifest-sha512.txt (or manifest-sha256.txt, depending on which was
    #                               used)
    #     in the format:
    #       checksum filepath
    #     NOTE: for now, don't allow any spaces, %, or linebreaks in file name
    @validator('File')
    @classmethod
    def check_singular_path_subdirectory(cls, values):
        for v in values:
            # TODO: Don't allow remote files, yet... Separate tag? RemoteFile?
            if len(v.Path) > 1 :
                raise ValueError("Please create a separate @File tag for each recorded file.")
            if len(v.Subdirectory) > 1:
                raise ValueError("MEDFORD does not currently support copying a file multiple times through one tag. " + 
                                "Please use a separate @File tag for each output file.")
            v = create_new_bagit_loc(v, "local")
        return values

    @validator('Data')
    @classmethod
    def create_bag_names(cls, values) :
        for dtentry in values :
            if dtentry.Primary:
                for dentry in dtentry.Primary:
                    dentry = create_new_bagit_loc(dentry, "local")
            if dtentry.Copy:
                for dentry in dtentry.Copy:
                    dentry = create_new_bagit_loc(dentry, "local")
            if dtentry.Ref:
                for dentry in dtentry.Ref:
                    dentry = create_new_bagit_loc(dentry, "remote")

        return values
    
    @root_validator
    @classmethod
    def create_list_things_to_copy(cls, values) :
        to_bag = []
        to_bag_and_rm = []
        if values.get("Files") and len(values.get("Files")) > 0 :
            all_to_copy.extend(values.get("Files"))
        
        for major in ["Data", "Software"] :
            if values.get(major) :
                for maj in values.get(major) :
                    if maj.Ref and len(maj.Ref) > 0 :
                        to_bag_and_rm.extend(maj.Ref)
                    if maj.Copy and len(maj.Copy) > 0:
                        to_bag.extend(maj.Copy)
                    if maj.Primary and len(maj.Primary) > 0:
                        to_bag.extend(maj.Primary)

        values["to_bag"] = to_bag
        values["to_bag_and_rm"] = to_bag_and_rm
        return values

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: List[Data]

    # TODO: FIX
    #@validator('Data')
    #@classmethod
    #def check_at_least_one_recorded(cls, v) :
    #    if not len(v['Primary']) > 0:
    #        raise ValueError('There must be at least 1 data field flagged as "recorded" for the BCO-DMO format,' +
    #                            ' to mark the new data being submitted.')
    #    return v

    Contributor: List[Contributor]
    Project: List[Project]
    Expedition: List[Expedition]

    # https://github.com/samuelcolvin/pydantic/issues/506
    # Check for at least one acceptable form of cruise identifier.
    @validator('Expedition')
    @classmethod
    def check_at_least_one_identifier(cls, v) :
        values = {key:value for key, value in v[0].__dict__.items() if not key.startswith('__') and not callable(key)}
        has_shipname = values['ShipName'] is not None and values['CruiseID'] is not None
        has_mooring = values['MooringID'] is not None 
        has_divenumber = values['DiveNumber'] is not None 
        if not any([has_shipname, has_mooring, has_divenumber]) :
            raise ValueError('BCO-DMO requires at least one cruise identifier. Your choices are: \n' +
                                '     ShipName and CruiseID, MooringID, or DiveNumber.')
        return v
    