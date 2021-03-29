
#run this from R2
setwd("/cenhome/dms-p0-992/moran331/Analysis_Results/PL94_Experiments/")

cons_geos=c("state","county","tract","block")
tables = c("pl94", "p1")
tables2 = c("PL94", "P1")

geolevels = c('State', 'County', 'Tract', 'Block', 'SLDU', 'SLDL')

width = 1200
height = 1000
pointsize = 14.5

table = tables[1]
geo = geolevels[1]

epsilon = c(0,0.01,0.1,0.25,0.5,1,10,2,3,5)

col1 = "grey"
col2 = "red"
col3 = "black"

yaxis_title = "Accuracy"
xaxis_title  = "Privacy-Loss Budget"
xtick = seq(0,1,0.25)

geo = geolevels[4]
table = tables[1]
data=read.csv(paste0("csv/",table,"_",geo,".csv"))[16,-1]


plot(epsilon, as.numeric(c(0,data)), type="b", col=col3 , pch = 20, main = paste0(geo, " level accuracy v. privacy loss"), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
    
    #png(paste0("Block_accuracy_", alphas[i],"_c1",cons_geo,"v2.png"), width = width, height = height, res =100, pointsize=pointsize)
    plot( c(x,x2)[ind],c(y,y2)[ind], col=col3 ,type="b", pch = 15, main = paste0("Block level PL94-171 accuracy v. privacy loss for alpha = ", alpha2," , c1", cons_geo), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
    #dev.off()
}



i=1
    alpha = get(alphas[i])
    alpha2 = alpha_num[i]
    png(paste0("BlockPL94_accuracy_", alphas[i],"v2.png"), width = width, height = height, res =100, pointsize=pointsize)
    par(mfrow=c(2,2), mar=c(4.1,4.4,2.1,1.1),oma=c(0,0,2,0))
    for(j in 1:4){
        cons_geo = cons_geos[j]
        geo = "Block"
        data_pl94=read.csv(paste0("analysis/",tables[1],"_c1",cons_geo,"_",geo,".csv"))[16,-1]
        data_pl94_2=read.csv(paste0("analysis/add_epsilon/",tables2[1],"_c1",cons_geo,"_",geo,"2.csv"))[16,-1]
        #Block level PL94-171 accuracy v. privacy loss for alpha = {}
        #pl94
        x=c(0,0.25,0.5,1,3,10);y= c(0,as.numeric(data_pl94[alpha]))
        x2=epsilon2;y2=as.numeric(data_pl94_2)

        ind = order(c(x,x2))

        plot( c(x,x2)[ind],c(y,y2)[ind], col=col3 ,type="b", pch = 15, main = paste0("c1", cons_geo), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
}
title(paste0("Block level PL94-171 accuracy v. privacy loss for alpha = ", alpha2), outer=TRUE) 
dev.off()


i=1
    alpha = get(alphas[i])
    alpha2 = alpha_num[i]
    png(paste0("TractPL94_accuracy_", alphas[i],"v2.png"), width = width, height = height, res =100, pointsize=pointsize)
    par(mfrow=c(2,2), mar=c(4.1,4.4,2.1,1.1),oma=c(0,0,2,0))
    for(j in 1:4){
        cons_geo = cons_geos[j]
        geo = "Tract"
        data_pl94=read.csv(paste0("analysis/",tables[1],"_c1",cons_geo,"_",geo,".csv"))[16,-1]
        data_pl94_2=read.csv(paste0("analysis/add_epsilon/",tables2[1],"_c1",cons_geo,"_",geo,"2.csv"))[16,-1]
        #Block level PL94-171 accuracy v. privacy loss for alpha = {}
        #pl94
        x=c(0,0.25,0.5,1,3,10);y= c(0,as.numeric(data_pl94[alpha]))
        x2=epsilon2;y2=as.numeric(data_pl94_2)

        ind = order(c(x,x2))

        plot( c(x,x2)[ind],c(y,y2)[ind], col=col3 ,type="b", pch = 15, main = paste0("c1", cons_geo), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
}
title(paste0("Tract level PL94-171 accuracy v. privacy loss for alpha = ", alpha2), outer=TRUE) 
dev.off()


i=1
    alpha = get(alphas[i])
    alpha2 = alpha_num[i]
    png(paste0("CountyPL94_accuracy_", alphas[i],"v2.png"), width = width, height = height, res =100, pointsize=pointsize)
    par(mfrow=c(2,2), mar=c(4.1,4.4,2.1,1.1),oma=c(0,0,2,0))
    for(j in 1:4){
        cons_geo = cons_geos[j]
        geo = "County"
        data_pl94=read.csv(paste0("analysis/",tables[1],"_c1",cons_geo,"_",geo,".csv"))[16,-1]
        data_pl94_2=read.csv(paste0("analysis/add_epsilon/",tables2[1],"_c1",cons_geo,"_",geo,"2.csv"))[16,-1]
        #Block level PL94-171 accuracy v. privacy loss for alpha = {}
        #pl94
        x=c(0,0.25,0.5,1,3,10);y= c(0,as.numeric(data_pl94[alpha]))
        x2=epsilon2;y2=as.numeric(data_pl94_2)

        ind = order(c(x,x2))

        plot( c(x,x2)[ind],c(y,y2)[ind], col=col3 ,type="b", pch = 15, main = paste0("c1", cons_geo), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
}
title(paste0("County level PL94-171 accuracy v. privacy loss for alpha = ", alpha2), outer=TRUE) 
dev.off()

i=1
    alpha = get(alphas[i])
    alpha2 = alpha_num[i]
    png(paste0("StatePL94_accuracy_", alphas[i],"v2.png"), width = width, height = height, res =100, pointsize=pointsize)
    par(mfrow=c(2,2), mar=c(4.1,4.4,2.1,1.1),oma=c(0,0,2,0))
    for(j in 1:4){
        cons_geo = cons_geos[j]
        geo = "State"
        data_pl94=read.csv(paste0("analysis/",tables[1],"_c1",cons_geo,"_",geo,".csv"))[16,-1]
        data_pl94_2=read.csv(paste0("analysis/add_epsilon/",tables2[1],"_c1",cons_geo,"_",geo,"2.csv"))[16,-1]
        #Block level PL94-171 accuracy v. privacy loss for alpha = {}
        #pl94
        x=c(0,0.25,0.5,1,3,10);y= c(0,as.numeric(data_pl94[alpha]))
        x2=epsilon2;y2=as.numeric(data_pl94_2)

        ind = order(c(x,x2))

        plot( c(x,x2)[ind],c(y,y2)[ind], col=col3 ,type="b", pch = 15, main = paste0("c1", cons_geo), ylab=yaxis_title, xlab=xaxis_title, ylim = c(0,1))
}
title(paste0("State level PL94-171 accuracy v. privacy loss for alpha = ", alpha2), outer=TRUE) 
dev.off()