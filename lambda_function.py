import os
import json
import subprocess

import boto3
from botocore.config import Config

from urllib import request
import zipfile

'''
    @author: Pietro Cinaglia
    @description: This is a non-exhaustive adaptation of the lambda function for testing purpose only. The paths for a generic sample are already defined in the function, so you don't have to configure a trigger to test this function.
'''
ENV = '/tmp'
HISAT2_LOCAL_PATH = ENV
EFS_PATH = '/mnt/efs1'
OUTPUT_DIR = ENV

def lambda_handler(event, context):
        
    os.chdir(ENV)
    
    sample = ['SAMPLE1_chrX_1.fastq','SAMPLE1_chrX_2.fastq']
    output_filename = 'SAMPLE1_output.sam'
    ref_genome = 'chrX_tran'

    retrieveInputs(sample, '/tmp')

    setEnvironment('local')

    syncReferenceGenome(EFS_PATH, '', ref_genome) 
    
    ls_out, ls_err = execute('date')
    print(ls_out)
    stdout, stderr = hisat2(EFS_PATH + '/' + ref_genome, sample[0], sample[1], OUTPUT_DIR + '/' + output_filename)
    print(stdout)
    print(stderr)
    ls_out, ls_err = execute('date')
    print(ls_out)
    
    ls_out, ls_err = execute('ls ' + OUTPUT_DIR)
    print(ls_out)
    
    output_file_size = get_size(OUTPUT_DIR + '/' + output_filename)
    print(output_file_size)
    
    return {'log': json.dumps(stdout)}

def execute(cmd):
    print(cmd)
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        p.wait()
    except AttributeError as error:
        return -1
    return p.communicate()

def hisat2(ref_genome, in_fastq1, in_fastq2, out_file):
    cmd = './hisat2 -x ' + ref_genome + ' -1 ' + in_fastq1 + ' -2 ' + in_fastq2 + ' -S ' + out_file
    stdout, stderr = execute(cmd)
    return stdout, stderr

def setEnvironment(path='local'):
    if not os.path.isdir(OUTPUT_DIR):
        stdout, stderr = execute('mkdir -p ' + OUTPUT_DIR + ' && chmod -R 777 ' + OUTPUT_DIR)
        print('Output folder created with (777) permissions.')
        print(stderr)
        
    if path == 'local':
        if not os.path.exists( ENV+'/hisat2' ):
            execute('cp /opt/hisat2/* ./ && chmod -R 777 ./')
            print("Hisat2 is ready to use.")
        else:
            print("Hisat2 found.")
        return
        
    elif path == 'remote':
        if os.path.isdir(HISAT2_LOCAL_PATH):
            print("Hisat2 found.")
            return
        request.urlretrieve("https://cloud.biohpc.swmed.edu/index.php/s/oTtGWbWjaxsQ2Ho/download", "hisat2.zip")
        with zipfile.ZipFile("hisat2.zip", 'r') as zip_ref:
            zip_ref.extractall('./')
        print("Hisat2 is now available.")
        return

def retrieveInputs(sample, local='/tmp'):
    #request.urlretrieve("https://trace.ncbi.nlm.nih.gov/Traces?run=SRR21746686", "SRR21746686.fastq.gz")

    config = Config(connect_timeout=5, retries={'max_attempts': 0})
    s3 = boto3.client('s3', config=config)
    
    s3.download_file('rnaseqgenomes', 'samples_chrX/' + sample[0], local+'/'+sample[0])
    s3.download_file('rnaseqgenomes', 'samples_chrX/' + sample[1], local+'/'+sample[1])

    '''
    my_bucket = 'rnaseqgenomes'
    prefix = 'grch38_chrX/'
    resource = boto3.resource('s3')
    download_dir(s3, resource, my_bucket, prefix, local)
    '''

def download_dir(client, resource, bucket, prefix, local='/tmp'):

    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=prefix):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                download_dir(client, resource, subdir.get('Prefix'), local, bucket)
        for file in result.get('Contents', []):
            dest_pathname = os.path.join(local, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            if not file.get('Key').endswith('/'):
                resource.meta.client.download_file(bucket, file.get('Key'), dest_pathname)

def syncReferenceGenome(location, prefix='', genomeFile=None, clean=True):
    
    if genomeFile is not None:
        if os.path.exists( location + '/' + genomeFile + '.1.ht2' ):
            print("Reference genome (" + genomeFile + ") found.")
            return
    else:
        if os.path.exists( location + '/genome.1.ht2' ):
            print("Reference genome found.")
            return
        
    if not os.path.exists( location + '/grch38_genome.tar.gz' ):
        s3 = boto3.client('s3')
        s3.download_file('genome-idx', 'hisat/grch38_genome.tar.gz', location + '/grch38_genome.tar.gz')
        
    if not os.path.isdir( location + '/' + prefix ):
        execute('mkdir ' + location + '/' + prefix)
    
    if len( os.listdir(location + prefix) ) == 0:
        with zipfile.ZipFile(location + '/grch38_genome.tar.gz', 'r') as zip_ref:
            zip_ref.extractall('./' + prefix)
        if clean:
            execute('rm ' + location + '/grch38_genome.tar.gz')
    
def get_size(path):
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024*1024:
        return f"{round(size/1024, 2)} KB"
    elif size < 1024*1024*1024:
        return f"{round(size/(1024*1024), 2)} MB"
    elif size < 1024*1024*1024*1024:
        return f"{round(size/(1024*1024*1024), 2)} GB"