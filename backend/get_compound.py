import requests

def download_mol_file(filename, compound_name):
    """Download MOL file from PubChem"""
    try:
        # Get compound CID
        search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/MolecularFormula/JSON"
        response = requests.get(search_url, timeout=600)
        
        if response.status_code == 200:
            data = response.json()
            cid = data['PropertyTable']['Properties'][0]['CID']
            
            # Download MOL file
            mol_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
            mol_response = requests.get(mol_url, timeout=600)
            
            if mol_response.status_code == 200:
                with open(filename, 'w') as f:
                    f.write(mol_response.text)
                print(f"Downloaded {filename}")
                return True
    except Exception as e:
        print(f"Download failed: {e}")
    
    return False

def get_compound_info(compound_name):
    """Get additional compound information from PubChem"""
    try:
        info_url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{compound_name}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
        )
        response = requests.get(info_url, timeout=600)
        if response.status_code == 200:
            data = response.json()
            props_list = data.get('PropertyTable', {}).get('Properties', [])
            if not props_list:
                return "No compound information found."
            props = props_list[0]
            iupac = props.get('IUPACName', 'N/A')
            info_lines = [
                f"Molecular Formula: {props.get('MolecularFormula', 'N/A')}",
                f"Molecular Weight: {props.get('MolecularWeight', 'N/A')}",
                f"IUPAC Name: {iupac[:50]}..." if iupac and len(iupac) > 50 else f"IUPAC Name: {iupac}"
            ]
            return "\n".join(info_lines)
    except Exception as e:
        print(f"Error getting compound info: {e}")