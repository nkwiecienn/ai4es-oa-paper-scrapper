from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ImageInfo:
    placeholder: str
    caption: str
    path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "placeholder": self.placeholder,
            "caption": self.caption,
            "path": self.path
        }

@dataclass
class TableInfo:
    csv_path: str
    table_index: int
    global_index: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "csv_path": self.csv_path,
            "table_index": self.table_index,
            "global_index": self.global_index
        }

@dataclass
class SectionInfo:
    heading: str
    tables: List[TableInfo] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    md_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "heading": self.heading,
            "tables": [t.to_dict() for t in self.tables],
            "images": [i.to_dict() for i in self.images],
            "md_path": self.md_path
        }

@dataclass
class DocumentInfo:
    paper_id: str
    source: str
    
    pmcid: Optional[str] = None
    arxiv_id: Optional[str] = None
    extraction_method: Optional[str] = None
    
    md_path: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    
    authors: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    
    sections: List[SectionInfo] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        res = {
            "paper_id": self.paper_id,
            "source": self.source,
            "authors": self.authors,
            "emails": self.emails,
        }
        if self.pmcid:
            res["pmcid"] = self.pmcid
        if self.arxiv_id:
            res["arxiv_id"] = self.arxiv_id
        if self.extraction_method:
            res["extraction_method"] = self.extraction_method
        if self.md_path:
            res["md_path"] = self.md_path
        if self.html_path:
            res["html_path"] = self.html_path
        if self.pdf_path:
            res["pdf_path"] = self.pdf_path
            
        res["sections"] = [s.to_dict() for s in self.sections]
        return res
