from beaker import Application, ReservedGlobalStateValue, Authorize
from beaker.application import Application
from pyteal.ast import abi
from beaker import *
from pyteal import Expr, TealType, abi, Approve, Global, Reject, Subroutine
from pyteal import *
from beaker.decorators import Authorize
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar
import pyteal
import csv
from pyteal.ast import App

# yt series to help one vid from it is: https://www.youtube.com/watch?v=NIPCGprfgoc

from pyteal import (
    And,
    Assert,
    AssetHolding,
    Expr,
    Global,
    Int,
    Seq,
    SubroutineFnWrapper,
    TealType,
    Txn,
)
from pyteal.types import require_type

_all_ = [
    "Authorize",
    "authorize",
    "AuthCallable",
]

VALID_CODES = [  # read from a txt file
    "1719471422",
    "8904193011",
    "1362006803",
    "3691176516",
    "2899819217",
    "8742056913",
    "5928374610",
    "7081562349",
    "3619842750",
    "1234567890"
    # Make a huge list of all of the valid identifcation codes or examples of them to check for validity
]
PATIENTS = [
    "87-42-15-6",
    "18-37-46-2",
    "39-28-47-1",
    "50-69-13-8",
    "72-90-84-5",
    "89-43-27-1",
    "61-32-45-8",
    "75-98-02-3",
    "42-61-89-7",
    "50-18-37-2",
]
AuthCallable = Callable[[Expr], Expr]
"""A function that takes Txn.sender() and returns a condition to assert"""


class MyState:
    identification = ReservedGlobalStateValue(
        stack_type=TealType.uint64,
        max_keys=10,  # sets the maximum limit for the identification
        descr="Identification code with maxiumum limit of 10 characters please enter to be verified",
    )


app = Application("hello_world", state=ReservedGlobalStateValue(TealType.uint64, 10))


@app.external  # this method allows the user to change the identification code based on their personal information
def set_reserved_app_state_val(k: abi.String, v: abi.Uint64) -> Expr:
    return MyState.identification[k].set(v.get())


# once authorized with validcode subroutine, ONLY THEN will the getPatient method is called.
@app.external  # this method checks whether the identification is valid and then provides access to the genetic info
def getThePatientInfo(
    k: abi.String, filename: abi.String, patientID: abi.String, *, output: abi.String
) -> Expr:
    tsvfile = filename + +Bytes(".tsv")
    patient = patientID
    return (
        If(
            validcode(k)
        ).Then(  # if valid it will output patient data; else it will say invalid
            If((read_file_method(tsvfile))).Then(output.set(get_patient_data(patient)))
        )
        # .Then(output.set("Welcome user " + k + str(MyState.identification[k])))
        .Else(output.set("Invalid Identification Code, Please Try Again"))
    )


# once both identification are authorized the data transfer across physicians (within a single healthcare facility) is made


# maybe a second method that has data transfer across multiple healthcare facilities
@app.external
def transferPatientData(md1: abi.String, md2: abi.String, p: abi.String) -> Expr:
    return If(validcode(md1) and validcode(md2)).Then(get_patient_data(p))


# I dont get how this would work


@app.external
def read_state(num: abi.Uint64, *, output: abi.String) -> Expr:
    return output.set(str(MyState.identification[num]))


# if user is opting in then transaction is approved
@app.opt_in
def opt_in() -> Expr:
    return Approve()


# if user is opting out then transaction is rejected
@app.close_out
def close_out() -> Expr:
    return Reject()


# always let an account opt in and out of the smart contract
@app.clear_state
def clear_state() -> Expr:
    return Approve()


# update the transaction
@app.update
def update() -> Expr:
    return Approve()


# delete transaction authorized so that only the creator can have access
@app.delete(authorize=Authorize.only(Global.creator_address()))
def delete() -> Expr:
    return Approve()


# below are subroutine methods in order to apply logic to this contract


# provides authorization since the Or is a boolean
# Chat.GPT fixed the original method you had and simplfied it
@Subroutine(TealType.uint64)
def validcode(code: abi.String) -> Expr:
    is_valid_code = Or(*[code.get() == Bytes(valid_code) for valid_code in VALID_CODES])

    return is_valid_code


# like environmental and clinical (age, sex, etc) as well as genomic and protein based*******
# maybe multiple methods for different types of data?
# defines a global array that has the patient data
file_array = []


# this method is called and takes a file name argument that is in this format: PatientName.txt
# if the file doesn't exist itll return true becuase (1 equals 1) if it does exist itll return false becuase 0!=1


@pyteal.Subroutine(TealType.uint64)
def read_file_method(filename):
    try:
        with open(filename, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            file_lines = []
            for row in reader:
                file_lines.append(row)
        App.globalPut(file_array, file_lines)
        return Int(1) == Int(1)

    except FileNotFoundError:
        return Int(0) == Int(1)


import csv


@Subroutine(TealType.bytes)
def get_patient_data(patient_id: abi.String):
    try:
        with open("patients.tsv") as f:
            reader = csv.reader(f, delimiter="\t")

            for row in reader:
                if row[0] == patient_id.get():
                    return Bytes(",".join(row))
    except Exception:
        return Bytes("Error")


# This method takes in a name sets a file to name.txt and adds the data that the method recieves as an argument
@Subroutine(TealType.none)
def add_patient_data(name, data):
    patient = Txn.sender() + Bytes(",") + data

    filename = name + Bytes(".tsv")

    return Seq(
        [App.Open(filename, App.AppendOnly), App.Write(patient), App.Close(), Int(1)]
    )


# steps for this application
# Step 1: user goes to the getPatientData method and inputs their code and patient name and what type of data they want
# Step 2(a): After verifying it will open that patient file and put it into an array
# Step 2(c): After verifying if the patient name doesn't exist, error message will show
# Step 2(c): If verfying fails then code will return an error message
# Step 3: Based on the last argument (data type) the getPatientData method will call a subroutine method that returns that specfic data
# Step 4: getPatientData returns the patient data and code ends.
