export type Point=[number,number];export type Outline=Point[];
export interface User{id:number;email:string;name:string;role:'admin'|'analyst'|'viewer'}
export interface Template{id:number;code:string;name:string;labels:string[];points:Outline;convention:string}
export interface Collection{id:number;code:string;name:string;template_id:number;protocol:string;source_file:string}
export interface Specimen{id:number;collection_id?:number;code:string;name:string;points:Outline;source_note:string}
export interface ShapeRow extends Specimen{centroid:Point;centroid_size:number;preshape:Outline;rotation:number[][];rotation_determinant:number;aligned:Outline;gpa_distance:number;scores:number[];reconstruction:Outline;residual:number}
export interface Mode{index:number;singular_value:number;eigenvalue:number;explained_ratio:number;sd:number;loading:Outline;minus_2sd:Outline;plus_2sd:Outline}
export interface PCA{arithmetic_mean:Outline;mean_norm:number;singular_values:number[];eigenvalues:number[];explained_ratio:number[];active_rank:number;retained_explained_ratio:number|null;retained:number;requested:number;noise_floor:number;has_variation:boolean;all_scores:number[][];scores:number[][];modes:Mode[];total_centered_ss:number}
export interface Snapshot{collection:Collection;template:Template;specimens:Specimen[]}
export interface Result{specimens:ShapeRow[];labels:string[];gpa_mean:Outline;gpa_mean_norm:number;reference_normalized:Outline;history:{iteration:number;objective:number;mean_delta:number|null;roundoff_increase?:boolean;roundoff_bound?:number}[];iterations:number;converged:boolean;effective_tolerance:number;termination:{reason:string;checked_iteration:number};determinant_min:number;pca:PCA;mean_difference:number;fingerprint:string;snapshot:Snapshot;scope:string}
export interface ComparisonSpecimen{code:string;name:string|null;status:'matched'|'added'|'removed';points_changed:boolean;gpa_distance:number|null;gpa_distance_previous:number|null;gpa_distance_delta:number|null;residual:number|null;residual_previous:number|null;residual_delta:number|null}
export interface RunComparison{source_run_id:number;source_status:string;result_available:boolean;added:ComparisonSpecimen[];removed:ComparisonSpecimen[];unchanged:ComparisonSpecimen[];label_order_changed:boolean;labels_previous:string[];labels_current:string[];template_changed:boolean;collection_changed:boolean;note:string}
export interface Run{id:number;name:string;collection_id:number;retained:number;tolerance:number;status:'queued'|'running'|'completed'|'failed';snapshot:Snapshot;result:Result;error:string;source_run_id:number|null;recalculation_key:string|null;created_at:string}
export interface RunPage{run:Run;comparison:RunComparison|null;provenance:Run[]}
export interface Note{id:number;name:string;run_id:number;specimen_id:number;protocol:string;status:'draft'|'approved'|'rejected';reviewer_note:string;reviewed_by:string;created_at:string}
