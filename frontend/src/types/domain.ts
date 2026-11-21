export type Farm = {id: string; name: string; owner_id:string; officer_id:string|null; state:string; district:string; village:string; location:string; survey_number:string; area:number; area_unit:string};
export type Field = {id:string;name:string;area:number;soil_type:string};
export type Measurement = {parameter:string;value:number;unit:string;method:string};
export type SoilSample = {id:string; farm_id:string;field_id:string|null;sample_code:string;collected_on:string;location:string;laboratory:string;status:'draft'|'submitted';climate:Record<string,string|number|null>;measurements:Measurement[];reviews?:{id:string;remarks:string;created_at:string}[]};
